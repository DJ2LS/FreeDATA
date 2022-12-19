#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: DJ2LS
python3 send_file.py --file cleanup.sh --dxcallsign DN2LS-0 --mycallsign DN2LS-2 --attempts 3

"""

import argparse
import socket
import json

# --------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=3000, help="Set socket listening port.", type=int)
parser.add_argument('--host', dest="socket_host", default='localhost', help="Set the host, the socket is listening on.", type=str)
parser.add_argument('--dxcallsign', dest="dxcallsign", default='AA0AA', help="Select the destination callsign", type=str)
parser.add_argument('--mycallsign', dest="mycallsign", default='AA0AA', help="Select the own callsign", type=str)
parser.add_argument('--ping', dest="ping", action="store_true", help="Send PING", type=str)
parser.add_argument('--cq', dest="cq", action="store_true", help="Send CQ", type=str)

args = parser.parse_args()

HOST, PORT = args.socket_host, args.socket_port
dxcallsign = args.dxcallsign
mycallsign = args.mycallsign

# our command we are going to send
if args.ping:
    command = {"type": "ping",
               "command": "ping",
               "dxcallsign": dxcallsign,
               "mycallsign": mycallsign,
               }
if args.cq:
    command = {"type": "broadcast",
               "command": "cqcqcq",
               "mycallsign": mycallsign,
               }
command = json.dumps(command)
command = bytes(command + "\n", 'utf-8')
# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(command)
