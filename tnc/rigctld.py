#!/usr/bin/env python3
import socket
import logging
# class taken from darsidelemm
# rigctl - https://github.com/darksidelemm/rotctld-web-gui/blob/master/rotatorgui.py#L35
#
# modified and adjusted to FreeDATA needs by DJ2LS

# set global hamlib version
hamlib_version = 0

class radio():
    """ rotctld (hamlib) communication class """
    # Note: This is a massive hack. 

    def __init__(self, hostname="localhost", port=4532, poll_rate=5, timeout=5):
        """ Open a connection to rotctld, and test it for validity """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)

        self.hostname = hostname
        self.port = port


    def open_rig(self, devicename, deviceport, hamlib_ptt_type, serialspeed, pttport, data_bits, stop_bits, handshake, rigctld_ip, rigctld_port):
        self.connect()
        logging.debug(f"Rigctl intialized")
        return True
    
    def connect(self):
        """ Connect to rotctld instance """
        self.sock.connect((self.hostname,self.port))
        ptt = self.get_ptt()
        if ptt == None:
            # Timeout!
            self.close()
            raise Exception("Timeout!")
        else:
            return ptt


    def close_rig(self):
        self.sock.close()


    def send_command(self, command):
        """ Send a command to the connected rotctld instance,
            and return the return value.
        """
        self.sock.sendall(command+b'\n')
        try:
            return self.sock.recv(1024)
        except:
            return None

    def get_mode(self):
        data = self.send_command(b"m")
        data = data.split(b'\n')
        mode = data[0]
        return mode.decode("utf-8")       
               
    def get_bandwith(self):
        data = self.send_command(b"m")
        data = data.split(b'\n')
        bandwith = data[1]
        return bandwith.decode("utf-8")
                
    def get_frequency(self):
        frequency =  self.send_command(b"f")
        return frequency.decode("utf-8")

    def get_ptt(self):
        return self.send_command(b"t")
                  
    def set_ptt(self, state):
        if state:
             self.send_command(b"T 1")
        else:
             self.send_command(b"T 0")
        return state        
        
