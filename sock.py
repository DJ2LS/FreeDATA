#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import socketserver
import threading
import logging
import json
import asyncio

import static
import data_handler
import helpers


class CMDTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):

        encoding = 'utf-8'
        #data = str(self.request.recv(1024), 'utf-8')

        data = bytes()
        while True:
            chunk = self.request.recv(8192)  # .strip()
            data += chunk
            if chunk.endswith(b'\n'):
                break
        data = data[:-1]  # remove b'\n'
        data = str(data, 'utf-8')

        # SOCKETTEST ---------------------------------------------------
        if data == 'SOCKETTEST':
            #cur_thread = threading.current_thread()
            response = bytes("WELL DONE! YOU ARE ABLE TO COMMUNICATE WITH THE TNC", encoding)
            self.request.sendall(response)

        # CQ CQ CQ -----------------------------------------------------
        if data == 'CQCQCQ':
            asyncio.run(data_handler.transmit_cq())
            # asyncio.run(asyncbg.call(data_handler.transmit_cq))
            #######self.request.sendall(b'CALLING CQ')

        # PING ----------------------------------------------------------
        if data.startswith('PING:'):
            # send ping frame and wait for ACK
            pingcommand = data.split('PING:')
            dxcallsign = pingcommand[1]
            # data_handler.transmit_ping(dxcallsign)
            ##loop = asyncio.get_event_loop()
            # loop.create_task(data_handler.transmit_ping(dxcallsign))
            # loop.run()

            # asyncio.new_event_loop()
            # asyncio.ensure_future(data_handler.transmit_ping(dxcallsign))

            asyncio.run(data_handler.transmit_ping(dxcallsign))

            # asyncio.create_task(data_handler.transmit_ping(dxcallsign))
            # asyncio.run(data_handler.transmit_ping(dxcallsign))

        # ARQ CONNECT TO CALLSIGN ----------------------------------------
        if data.startswith('ARQ:CONNECT:'):
            arqconnectcommand = data.split('ARQ:CONNECT:')
            dxcallsign = arqconnectcommand[1]
            static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
            static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)

            if static.ARQ_STATE == 'CONNECTED':
                # here we could disconnect
                pass

            if static.TNC_STATE == 'IDLE':
                # here we send an "CONNECT FRAME

                #ARQ_CONNECT_THREAD = threading.Thread(target=data_handler.arq_connect, name="ARQ_CONNECT")
                # ARQ_CONNECT_THREAD.start()
                asyncio.run(data_handler.arq_connect())
                ########self.request.sendall(bytes("CONNECTING", encoding))
                # data_handler.arq_connect()
        # ARQ DISCONNECT FROM CALLSIGN ----------------------------------------
        if data == 'ARQ:DISCONNECT':

            #ARQ_DISCONNECT_THREAD = threading.Thread(target=data_handler.arq_disconnect, name="ARQ_DISCONNECT")
            # ARQ_DISCONNECT_THREAD.start()
            asyncio.run(data_handler.arq_disconnect())

            ########self.request.sendall(bytes("DISCONNECTING", encoding))
            # data_handler.arq_disconnect()

        if data.startswith('ARQ:OPEN_DATA_CHANNEL') and static.ARQ_STATE == 'CONNECTED':
            static.ARQ_READY_FOR_DATA = False
            static.TNC_STATE = 'BUSY'
            asyncio.run(data_handler.arq_open_data_channel())
            

        if data.startswith('ARQ:DATA:') and static.ARQ_STATE == 'CONNECTED' and static.ARQ_READY_FOR_DATA == True:

            static.TNC_STATE = 'BUSY'
            arqdata = data.split('ARQ:')
            data_out = bytes(arqdata[1], 'utf-8')

            ARQ_DATA_THREAD = threading.Thread(target=data_handler.arq_transmit, args=[data_out], name="ARQ_DATA")
            ARQ_DATA_THREAD.start()
            # asyncio.run(data_handler.arq_transmit(data_out))

        # SETTINGS AND STATUS ---------------------------------------------
        if data.startswith('SET:MYCALLSIGN:'):
            callsign = data.split('SET:MYCALLSIGN:')
            if bytes(callsign[1], encoding) == b'':
                self.request.sendall(b'INVALID CALLSIGN')
            else:
                static.MYCALLSIGN = bytes(callsign[1], encoding)
                static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)
                # self.request.sendall(static.MYCALLSIGN)
                logging.info("CMD | MYCALLSIGN: " + str(static.MYCALLSIGN))

        if data == 'GET:MYCALLSIGN':
            self.request.sendall(bytes(static.MYCALLSIGN, encoding))

        if data == 'GET:DXCALLSIGN':
            self.request.sendall(bytes(static.DXCALLSIGN, encoding))

        if data == 'GET:TNC_STATE':
            output = {
                "PTT_STATE": str(static.PTT_STATE),
                "CHANNEL_STATE": str(static.CHANNEL_STATE),
                "TNC_STATE": str(static.TNC_STATE),
                "ARQ_STATE": str(static.ARQ_STATE),
                "AUDIO_RMS": str(static.AUDIO_RMS),
                "BER": str(static.BER)
            }
            jsondata = json.dumps(output)
            self.request.sendall(bytes(jsondata, encoding))

        if data == 'GET:DATA_STATE':
            output = {
                "RX_BUFFER_LENGTH": str(len(static.RX_BUFFER)),
                "TX_N_MAX_RETRIES": str(static.TX_N_MAX_RETRIES),
                "ARQ_TX_N_FRAMES_PER_BURST": str(static.ARQ_TX_N_FRAMES_PER_BURST),
                "ARQ_TX_N_BURSTS": str(static.ARQ_TX_N_BURSTS),
                "ARQ_TX_N_CURRENT_ARQ_FRAME": str(int.from_bytes(bytes(static.ARQ_TX_N_CURRENT_ARQ_FRAME), "big")),
                "ARQ_TX_N_TOTAL_ARQ_FRAMES": str(int.from_bytes(bytes(static.ARQ_TX_N_TOTAL_ARQ_FRAMES), "big")),
                "ARQ_RX_FRAME_N_BURSTS": str(static.ARQ_RX_FRAME_N_BURSTS),
                "ARQ_RX_N_CURRENT_ARQ_FRAME": str(static.ARQ_RX_N_CURRENT_ARQ_FRAME),
                "ARQ_N_ARQ_FRAMES_PER_DATA_FRAME": str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME)
            }
            jsondata = json.dumps(output)
            self.request.sendall(bytes(jsondata, encoding))

        if data == 'GET:HEARD_STATIONS':
            output = []
            for i in range(0, len(static.HEARD_STATIONS)):
                output.append({"CALLSIGN": str(static.HEARD_STATIONS[i][0], 'utf-8'), "TIMESTAMP": static.HEARD_STATIONS[i][1]})

            jsondata = json.dumps(output)
            self.request.sendall(bytes(jsondata, encoding))

        if data.startswith('GET:RX_BUFFER:'):
            data = data.split('GET:RX_BUFFER:')
            bufferposition = int(data[1]) - 1
            if bufferposition == -1:
                if len(static.RX_BUFFER) > 0:
                    self.request.sendall(static.RX_BUFFER[-1])

            if bufferposition <= len(static.RX_BUFFER) > 0:
                self.request.sendall(bytes(static.RX_BUFFER[bufferposition]))

        if data == 'DEL:RX_BUFFER':
            static.RX_BUFFER = []

        # self.request.close()


def start_cmd_socket():

    try:
        logging.info("SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: " + str(static.PORT))
        socketserver.TCPServer.allow_reuse_address = True  # https://stackoverflow.com/a/16641793
        cmdserver = socketserver.TCPServer((static.HOST, static.PORT), CMDTCPRequestHandler)
        cmdserver.serve_forever()

    finally:
        cmdserver.server_close()
