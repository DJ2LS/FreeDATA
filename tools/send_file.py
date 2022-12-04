#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: DJ2LS
python3 send_file.py --file cleanup.sh --dxcallsign DN2LS-0 --mycallsign DN2LS-2 --attempts 3

"""

import argparse
import socket
import base64
import json

# --------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=3000, help="Set socket listening port.", type=int)
parser.add_argument('--host', dest="socket_host", default='localhost', help="Set the host, the socket is listening on.", type=str)
parser.add_argument('--file', dest="filename", default='test.txt', help="Select the file we want to send", type=str)
parser.add_argument('--dxcallsign', dest="dxcallsign", default='AA0AA', help="Select the destination callsign", type=str)
parser.add_argument('--mycallsign', dest="mycallsign", default='AA0AA', help="Select the own callsign", type=str)
parser.add_argument('--attempts', dest="attempts", default='5', help="Amount of connection attempts", type=int)

args = parser.parse_args()


HOST, PORT = args.socket_host, args.socket_port
filename = args.filename
dxcallsign = args.dxcallsign
mycallsign = args.mycallsign
attempts = args.attempts

# open file by name
f = open(filename, "rb")
file = f.read()

# convert binary data to base64
base64_data = base64.b64encode(file).decode("UTF-8")

# our command we are going to send
command = {"type": "arq",
           "command": "send_raw",
           "parameter":
               [{"dxcallsign": dxcallsign,
                 "mycallsign": mycallsign,
                 "attempts": str(attempts),
                 "mode": "255",
                 "n_frames": "1",
                 "data": base64_data}
                ]
           }
command = json.dumps(command)
command = bytes(command + "\n", 'utf-8')
# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(command)
