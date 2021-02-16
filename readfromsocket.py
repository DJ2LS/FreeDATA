#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 21:53:35 2020

@author: parallels
"""

import socket
import sys
import argparse
import time




#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=3000, help="Set the port, the socket is listening on.", type=int) 
parser.add_argument('--data', dest="data", default=False, help="data", type=str)

args = parser.parse_args()

ip, port = "localhost", args.socket_port
message = args.data



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(ip)
        print(port)
        sock.connect((ip, port))
        sock.sendall(bytes(message, 'utf-8'))
        response = str(sock.recv(1024), 'utf-8')
        print("Received: {}".format(response))
