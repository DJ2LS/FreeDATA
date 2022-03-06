#!/usr/bin/env python3
import socket
import structlog
import log_handler
import logging
import time
import static
# class taken from darsidelemm
# rigctl - https://github.com/darksidelemm/rotctld-web-gui/blob/master/rotatorgui.py#L35
#
# modified and adjusted to FreeDATA needs by DJ2LS

# set global hamlib version
hamlib_version = 0

class radio():
    """rotctld (hamlib) communication class"""
    # Note: This is a massive hack. 

    def __init__(self, hostname="localhost", port=4532, poll_rate=5, timeout=5):
        """ Open a connection to rotctld, and test it for validity """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.settimeout(timeout)

        self.connected = False
        self.hostname = hostname
        self.port = port
        self.connection_attempts = 5

    def open_rig(self, devicename, deviceport, hamlib_ptt_type, serialspeed, pttport, data_bits, stop_bits, handshake, rigctld_ip, rigctld_port):
        """

        Args:
          devicename: 
          deviceport: 
          hamlib_ptt_type: 
          serialspeed: 
          pttport: 
          data_bits: 
          stop_bits: 
          handshake: 
          rigctld_ip: 
          rigctld_port: 

        Returns:

        """
        self.hostname = rigctld_ip
        self.port = int(rigctld_port)
        
       
        if self.connect():
            logging.debug(f"Rigctl intialized")
            return True
        else:
            structlog.get_logger("structlog").error("[RIGCTLD] Can't connect to rigctld!", ip=self.hostname, port=self.port)
            return False
            
    def connect(self):
        """Connect to rigctld instance"""
        if not self.connected:
            try:
                self.connection = socket.create_connection((self.hostname,self.port))
                self.connected = True
                structlog.get_logger("structlog").info("[RIGCTLD] Connected to rigctld!", ip=self.hostname, port=self.port)
                return True
            except Exception as e:
                # ConnectionRefusedError: [Errno 111] Connection refused
                self.close_rig()
                structlog.get_logger("structlog").warning("[RIGCTLD] Connection to rigctld refused! Reconnect...", ip=self.hostname, port=self.port, e=e)
                return False
    
    def close_rig(self):
        """ """
        self.sock.close()
        self.connected = False


    def send_command(self, command):
        """Send a command to the connected rotctld instance,
            and return the return value.

        Args:
          command: 

        Returns:

        """
        if self.connected:
            try:
                self.connection.sendall(command+b'\n')
            except:
                structlog.get_logger("structlog").warning("[RIGCTLD] Command not executed!", command=command, ip=self.hostname, port=self.port)
                self.connected = False

            try:
                return self.connection.recv(1024)
            except:
                structlog.get_logger("structlog").warning("[RIGCTLD] No command response!", command=command, ip=self.hostname, port=self.port)
                self.connected = False
        else:
            
            # reconnecting....
            time.sleep(0.5)
            self.connect()


    def get_mode(self):
        """ """
        try:
            data = self.send_command(b"m")
            data = data.split(b'\n')
            mode = data[0]
            return mode.decode("utf-8")       
        except:
            0
    def get_bandwith(self):
        """ """
        try:
            data = self.send_command(b"m")
            data = data.split(b'\n')
            bandwith = data[1]
            return bandwith.decode("utf-8")
        except:
            return 0
        
    def get_frequency(self):
        """ """
        try:
            frequency = self.send_command(b"f")
            return frequency.decode("utf-8")
        except:
            return 0
        
    def get_ptt(self):
        """ """
        try:
            return self.send_command(b"t")
        except:
            return False
        
    def set_ptt(self, state):
        """

        Args:
          state: 

        Returns:

        """
        try:
            if state:
                 self.send_command(b"T 1")
            else:
                 self.send_command(b"T 0")
            return state        
        except:
            return False
