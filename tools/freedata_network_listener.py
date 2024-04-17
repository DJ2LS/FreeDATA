#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
deprecated_daemon.py

Author: DJ2LS, January 2022

daemon for providing basic information for the freedata-server like audio or serial devices

"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel


import argparse
import socket
import structlog
import queue
import json
import base64
import os

log = structlog.get_logger("CLIENT")


split_char = b"\x00;"
# --------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--port', dest="socket_port", default=3000, help="Set the port, the socket is listening on.", type=int) 
parser.add_argument('--host', dest="socket_host", default='localhost', help="Set the host, the socket is listening on.", type=str)

args = parser.parse_args()

ip, port = args.socket_host, args.socket_port
connected = True
data = bytes()

"""
Nachricht
{'command': 'rx_buffer', 'data-array': [{'uuid': '8dde227d-3a09-4f39-b34c-5f8281d719d1', 'timestamp': 1672043316, 'dxcallsign': 'DJ2LS-1', 'dxgrid': 'JN48cs', 'data': 'bQA7c2VuZF9tZXNzYWdlADsxMjMAO2VkY2NjZDAyLTUzMTQtNDc3Ni1hMjlkLTFmY2M1ZDI4OTM4ZAA7VGVzdAoAOwA7cGxhaW4vdGV4dAA7ADsxNjcyMDQzMzA5'}]}
"""

def decode_and_save_data(encoded_data):
    decoded_data = base64.b64decode(encoded_data)
    decoded_data = decoded_data.split(split_char)

    if decoded_data[0] == b'm':
        print(jsondata)
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", uuid=decoded_data[3])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", message=decoded_data[4])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", filename=decoded_data[5])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", filetype=decoded_data[6])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", data=decoded_data[7])

        try:
            folderpath = "received"
            if not os.path.exists(folderpath):
                os.makedirs(folderpath)
            filename = decoded_data[8].decode("utf-8") + "_" + decoded_data[5].decode("utf-8")

            with open(f"{folderpath}/{filename}", "wb") as file:
                file.write(decoded_data[7])

            with open(f"{folderpath}/{decoded_data[8].decode('utf-8')}_msg.txt", "wb") as file:
                file.write(decoded_data[4])

        except Exception as e:
            print(e)

    else:
        print(decoded_data)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((ip, port))
    print(sock)
    while connected:
        chunk = sock.recv(1024)
        data += chunk
        if data.startswith(b"{") and data.endswith(b"}\n"):
            # split data by \n if we have multiple commands in socket buffer
            data = data.split(b"\n")
            # remove empty data
            data.remove(b"")

            # iterate through data list
            for command in data:

                jsondata = json.loads(command)

                if jsondata.get('command') == "tnc_state":
                    #pass
                    print(jsondata.get("routing_table"))

                if jsondata.get('freedata') == "freedata-server-message":
                    log.info(jsondata)

                if jsondata.get('ping') == "acknowledge":
                    log.info(f"PING {jsondata.get('mycallsign')} >><< {jsondata.get('dxcallsign')}", snr=jsondata.get('snr'), dxsnr=jsondata.get('dxsnr'))

                if jsondata.get('status') == 'receiving':
                    log.info(jsondata)

                if jsondata.get('command') == 'rx_buffer':
                    for rxdata in jsondata["data-array"]:
                        log.info(f"rx buffer {rxdata.get('uuid')}")
                        decode_and_save_data(rxdata.get('data'))

                if jsondata.get('status') == 'received' and jsondata.get('arq') == 'transmission':
                    decode_and_save_data(jsondata["data"])



            # clear data buffer as soon as data has been read
            data = bytes()


