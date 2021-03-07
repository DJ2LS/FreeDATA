#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 21:53:35 2020

@author: parallels
"""

import socket
import sys
import argparse
import random

#https://www.askpython.com/python/examples/generate-random-strings-in-python
def create_string(length):
    random_string = ''
    for _ in range(length):
    # Considering only upper and lowercase letters
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
    # Convert to lowercase if the flip bit is on
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
    # Keep appending random characters using chr(x)
        random_string += (chr(random_integer))
    print("STR:" + str(random_string))
    
    return random_string
    
    
    
    

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=9000, help="Set the port, the socket is listening on.", type=int) 
#parser.add_argument('--data', dest="data", default=False, help="data", type=str)
parser.add_argument('--random', dest="datalength", default=False, help="data", type=int)




args = parser.parse_args()


data = create_string(args.datalength)
data = bytes("ARQ:DATA:" + "" + data + "" + "\n", "utf-8")



#print(data)


HOST, PORT = "localhost", args.socket_port
#data = args.data

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    #sock.sendall(bytes(data + "\n", "utf-8"))
    sock.sendall(data)
    # Receive data from the server and shut down
    received = str(sock.recv(1024), "utf-8")

print("Sent:     {}".format(data))



