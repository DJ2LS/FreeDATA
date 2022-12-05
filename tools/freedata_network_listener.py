#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
daemon.py

Author: DJ2LS, January 2022

daemon for providing basic information for the tnc like audio or serial devices

"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel


import argparse
import socket
import structlog
import queue
import json


log = structlog.get_logger("CLIENT")

# --------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=3000, help="Set the port, the socket is listening on.", type=int) 

args = parser.parse_args()

ip, port = "localhost", args.socket_port

connected = True

data = bytes()
         
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((ip, port))
    
    while connected:
        chunk = sock.recv(2)
        data += chunk
        
        if data.endswith(b'\n'):

            jsondata = json.loads(data.split(b'\n')[0])
            data = bytes()

            if jsondata.get('command') == "tnc_state":
                pass
            
            if jsondata.get('freedata') == "tnc-message":
                log.info(jsondata)
