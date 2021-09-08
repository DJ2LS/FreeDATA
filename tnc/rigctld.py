#!/usr/bin/env python3
import socket
import logging
import static

# rigctl - https://github.com/darksidelemm/rotctld-web-gui/blob/master/rotatorgui.py#L35
# https://github.com/xssfox/freedv-tnc/blob/master/freedvtnc/rigctl.py


class Rigctld():
    """ rotctld (hamlib) communication class """
    # Note: This is a massive hack. 

    def __init__(self, hostname="localhost", port=4532, poll_rate=5, timeout=5):
        """ Open a connection to rotctld, and test it for validity """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)

        self.hostname = hostname
        self.port = port
        self.connect()
        logging.debug(f"Rigctl intialized")

    def get_model(self):
        """ Get the rotator model from rotctld """
        model = self.send_command(b'_')
        return model

    def connect(self):
        """ Connect to rotctld instance """
        self.sock.connect((self.hostname,self.port))
        model = self.get_model()
        if model == None:
            # Timeout!
            self.close()
            raise Exception("Timeout!")
        else:
            return model


    def close(self):
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

    def ptt_enable(self):
        logging.debug(f"PTT enabled")
        self.send_command(b"T 1")

    def ptt_disable(self):
        logging.debug(f"PTT disabled")
        self.send_command(b"T 0")
        
    def get_frequency(self):
        data = self.send_command(b"f")  
        if data is not None:
            data = data.split(b'\n')
            try:
                freq = int(data[0])/1000
            except:
                freq = static.HAMLIB_FREQUENCY
                #print("freq-err: " + str(data))
                #for i in range(len(data)):
                #    print(data[i])
                    
            return freq
         
    def get_mode(self):
        data = self.send_command(b"m")
        if data is not None:
            data = data.split(b'\n')  
            try:
                mode = str(data[0], "utf-8")
                bandwith = int(data[1])
            except:
                #print("mode-err: " + str(data))
                mode = static.HAMLIB_MODE
                bandwith = static.HAMLIB_BANDWITH
            return [mode, bandwith]

