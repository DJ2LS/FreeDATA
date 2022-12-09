#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enable --- python3.9 enable_disable_beacon.py --host 192.168.178.42 --interval 120 --enable
disable -- python3.9 enable_disable_beacon.py
@author: DJ2LS

"""

import argparse
import socket
import base64
import json

# --------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=3000, help="Set socket listening port.", type=int)
parser.add_argument('--host', dest="socket_host", default='localhost', help="Set the host, the socket is listening on.", type=str)
parser.add_argument('--interval', dest="interval", default=120, help="Interval in seconds", type=int)
parser.add_argument("--enable",dest="enable",action="store_true",help="Enable beacon",)


args = parser.parse_args()


HOST, PORT = args.socket_host, args.socket_port
interval = args.interval
enable = args.enable

if enable:
    # our command we are going to send
    command = {"type": "broadcast", "command": "start_beacon", "parameter": str(interval)}
else:
    command = {"type": "broadcast", "command": "stop_beacon"}


command = json.dumps(command)
command = bytes(command + "\n", 'utf-8')
# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(command)
