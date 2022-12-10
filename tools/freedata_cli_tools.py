#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: DJ2LS

"""

import argparse
import socket
import base64
import json
from pick import pick
import time
import sounddevice as sd

# --------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=3000, help="Set socket listening port.", type=int)
parser.add_argument('--host', dest="socket_host", default='localhost', help="Set the host, the socket is listening on.", type=str)
args = parser.parse_args()
HOST, PORT = args.socket_host, args.socket_port


def main_menu():
    while True:
        time.sleep(0.1)
        title = 'Please select a command you want to run: '
        options = ['BEACON', 'PING', 'ARQ', 'LIST AUDIO DEVICES']
        option, index = pick(options, title)

        # BEACON AREA
        if option == 'BEACON':
            option, index = pick(['5',
                                  '10',
                                  '15',
                                  '30',
                                  '45',
                                  '60',
                                  '90',
                                  '120',
                                  '300',
                                  '600',
                                  '900',
                                  '1800',
                                  '3600',
                                  'STOP BEACON',
                                  '----- BACK -----'], "Select beacon interval [seconds]")

            if option == '----- BACK -----':
                main_menu()
            elif option == 'STOP BEACON':
                run_network_command(HOST, PORT, {"type": "broadcast", "command": "stop_beacon"})
                return
            else:
                run_network_command(HOST, PORT, {"type": "broadcast", "command": "start_beacon", "parameter": str(option)})
                return

        elif option == 'PING':
            pass

        elif option == 'ARQ':
            option, index = pick(['DISCONNECT', '----- BACK -----'], "Select ARQ command")

            if option == '----- BACK -----':
                main_menu()
            else:
                run_network_command(HOST, PORT,{"type": "arq", "command": "disconnect"})

        elif option == 'LIST AUDIO DEVICES':

            devices = sd.query_devices(device=None, kind=None)
            device_list = []
            for device in devices:
                device_list.append(
                    f"{device['index']} - "
                    f"{sd.query_hostapis(device['hostapi'])['name']} - "
                    f"Channels (In/Out):{device['max_input_channels']}/{device['max_output_channels']} - "
                    f"{device['name']}")

            device_list.append('----- BACK -----')

            option, index = pick(device_list, "Audio devices")

            if option == '----- BACK -----':
                main_menu()

        else:
            pass


def run_network_command(host, port, command):
    command = json.dumps(command)
    command = bytes(command + "\n", 'utf-8')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        sock.connect((host, port))
        sock.sendall(command)


main_menu()