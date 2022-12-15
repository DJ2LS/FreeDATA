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
import base64

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


def decode_and_save_data(data):
    decoded_data = base64.b64decode(data)
    decoded_data = decoded_data.split(split_char)

    if decoded_data[0] == b'm':
        print(jsondata)
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", uuid=decoded_data[3])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", message=decoded_data[4])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", filename=decoded_data[5])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", filetype=decoded_data[6])
        log.info(f"{jsondata.get('mycallsign')} <<< {jsondata.get('dxcallsign')}", data=decoded_data[7])

        try:
            filename = decoded_data[8].decode("utf-8") + "_" + decoded_data[5].decode("utf-8")

            file = open(filename, "wb")
            file.write(decoded_data[7])
            file.close()
        except Exception as e:
            print(e)

    else:
        print(decoded_data)


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

            if jsondata.get('ping') == "acknowledge":
                log.info(f"PING {jsondata.get('mycallsign')} >><< {jsondata.get('dxcallsign')}", snr=jsondata.get('snr'), dxsnr=jsondata.get('dxsnr'))

            if jsondata.get('status') == 'receiving':
                log.info(jsondata)

            if jsondata.get('command') == 'rx_buffer':
                for rxdata in jsondata["data-array"]:
                    log.info(f"rx buffer {rxdata.get('uuid')}")
                    decode_and_save_data(rxdata.get('data'))

            if jsondata.get('status') == 'received':
                decode_and_save_data(jsondata["data"])


