#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS

# GET COMMANDS
            # "command" : "..."
            
            # SET COMMANDS
            # "command" : "..."
            # "parameter" : " ..."
            
            # DATA COMMANDS
            # "command" : "..."
            # "type" : "..."
            # "dxcallsign" : "..."
            # "data" : "..."


"""

import socketserver
import threading
import logging
import json
import asyncio
import time

import static
import data_handler
import helpers

import sys, os

class CMDTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print("Client connected...")    
        
        # loop through socket buffer until timeout is reached. then close buffer
        socketTimeout = time.time() + 3
        while socketTimeout > time.time():

            time.sleep(0.01)
            encoding = 'utf-8'
            #data = str(self.request.recv(1024), 'utf-8')

            data = bytes()
            
            # we need to loop through buffer until end of chunk is reached or timeout occured
            while True and socketTimeout > time.time():
                chunk = self.request.recv(1024)  # .strip()
                data += chunk
                if chunk.endswith(b'}\n'):# or chunk.endswith(b'}') or chunk.endswith(b'\n'):
                    break
            data = data[:-1]  # remove b'\n'
            data = str(data, 'utf-8')
            #print(data)
            
            if len(data) > 0:
                socketTimeout = time.time() + static.SOCKET_TIMEOUT
            
            # convert data to json object
            # we need to do some error handling in case of socket timeout

            try:
                
                received_json = json.loads(data)

            except json.decoder.JSONDecodeError as e:
                print("++++++++++++ START OF JSON ERROR +++++++++++++++++++++++")
                print(e)
                print("-----------------------------------")
                print(data)
                print("++++++++++++ END OF JSON ERROR +++++++++++++++++++++++++")
                received_json = {}
            
            try:

                # CQ CQ CQ -----------------------------------------------------
                if received_json["command"] == "CQCQCQ":
                    socketTimeout = 0
                    #asyncio.run(data_handler.transmit_cq())
                    CQ_THREAD = threading.Thread(target=data_handler.transmit_cq, args=[], name="CQ")
                    CQ_THREAD.start()

                # PING ----------------------------------------------------------
                if received_json["type"] == 'PING' and received_json["command"] == "PING":
                    # send ping frame and wait for ACK
                    print(received_json)
                    dxcallsign = received_json["dxcallsign"]
                    #asyncio.run(data_handler.transmit_ping(dxcallsign))
                    PING_THREAD = threading.Thread(target=data_handler.transmit_ping, args=[dxcallsign], name="CQ")
                    PING_THREAD.start()

                if received_json["type"] == 'ARQ' and received_json["command"] == "OPEN_DATA_CHANNEL":
                    static.ARQ_READY_FOR_DATA = False
                    static.TNC_STATE = 'BUSY'
                    
                    dxcallsign = received_json["dxcallsign"]
                    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
                    
                    asyncio.run(data_handler.arq_open_data_channel())
                    
                if received_json["type"] == 'ARQ' and received_json["command"] == "sendFile":# and static.ARQ_READY_FOR_DATA == True: # and static.ARQ_STATE == 'CONNECTED' :
                    static.TNC_STATE = 'BUSY'
                    
                    #on a new transmission we reset the timer
                    static.ARQ_START_OF_TRANSMISSION = int(time.time())
                    
                    dxcallsign = received_json["dxcallsign"]
                    mode = int(received_json["mode"])
                    n_frames = int(received_json["n_frames"])
                    filename = received_json["filename"]
                    filetype = received_json["filetype"]
                    data = received_json["data"]
                    checksum = received_json["checksum"]
                 
                    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
                    
                    ##dataframe = '{"filename": "'+ filename + '", "filetype" : "' + filetype + '", "data" : "' + data + '", "checksum" : "' + checksum + '"}'
                    dataframe = {"filename" : filename , "filetype" :filetype, "data" : data, "checksum" :checksum}

                    #data_out = bytes(received_json["data"], 'utf-8')
                    dataframe = json.dumps(dataframe)
                    data_out = bytes(dataframe, 'utf-8')

                   
                    
                    #ARQ_DATA_THREAD = threading.Thread(target=data_handler.arq_transmit, args=[data_out], name="ARQ_DATA")
                    #ARQ_DATA_THREAD.start()
                    
                    ARQ_DATA_THREAD = threading.Thread(target=data_handler.open_dc_and_transmit, args=[data_out, mode, n_frames], name="ARQ_DATA")
                    ARQ_DATA_THREAD.start()
                    # asyncio.run(data_handler.arq_transmit(data_out))

                # SETTINGS AND STATUS ---------------------------------------------
                if received_json["type"] == 'SET' and received_json["command"] == 'MYCALLSIGN':
                    callsign = received_json["parameter"]

                    if bytes(callsign, encoding) == b'':
                        self.request.sendall(b'INVALID CALLSIGN')
                    else:
                        static.MYCALLSIGN = bytes(callsign, encoding)
                        static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)
                        logging.info("CMD | MYCALLSIGN: " + str(static.MYCALLSIGN))
          
                if received_json["type"] == 'SET' and received_json["command"] == 'MYGRID':
                    mygrid = received_json["parameter"]

                    if bytes(mygrid, encoding) == b'':
                        self.request.sendall(b'INVALID GRID')
                    else:
                        static.MYGRID = bytes(mygrid, encoding)
                        logging.info("CMD | MYGRID: " + str(static.MYGRID))
                        
                                    
                if received_json["type"] == 'GET' and received_json["command"] == 'STATION_INFO':
                    output = {
                        "COMMAND": "STATION_INFO",
                        "TIMESTAMP" : received_json["timestamp"],
                        "MY_CALLSIGN": str(static.MYCALLSIGN, encoding),
                        "DX_CALLSIGN": str(static.DXCALLSIGN, encoding),
                        "DX_GRID": str(static.DXGRID, encoding),
                        "EOF" : "EOF",  
                    }
                    
                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))

                if received_json["type"] == 'GET' and received_json["command"] == 'TNC_STATE':
                    #print(static.SCATTER)
                    output = {
                        "COMMAND": "TNC_STATE",
                        "TIMESTAMP" : received_json["timestamp"],
                        "PTT_STATE": str(static.PTT_STATE),
                        "CHANNEL_STATE": str(static.CHANNEL_STATE),
                        "TNC_STATE": str(static.TNC_STATE),
                        "ARQ_STATE": str(static.ARQ_STATE),
                        "AUDIO_RMS": str(static.AUDIO_RMS),
                        "BER": str(static.BER),
                        "SNR": str(static.SNR),
                        "FREQUENCY" : str(static.HAMLIB_FREQUENCY),
                        "MODE" : str(static.HAMLIB_MODE),
                        "BANDWITH" : str(static.HAMLIB_BANDWITH),
                        "FFT" : str(static.FFT),
                        "SCATTER" : static.SCATTER,
                        "RX_BUFFER_LENGTH": str(len(static.RX_BUFFER)),
                        "TX_N_MAX_RETRIES": str(static.TX_N_MAX_RETRIES),
                        "ARQ_TX_N_FRAMES_PER_BURST": str(static.ARQ_TX_N_FRAMES_PER_BURST),
                        "ARQ_TX_N_BURSTS": str(static.ARQ_TX_N_BURSTS),
                        "ARQ_TX_N_CURRENT_ARQ_FRAME": str(int.from_bytes(bytes(static.ARQ_TX_N_CURRENT_ARQ_FRAME), "big")),
                        "ARQ_TX_N_TOTAL_ARQ_FRAMES": str(int.from_bytes(bytes(static.ARQ_TX_N_TOTAL_ARQ_FRAMES), "big")),
                        "ARQ_RX_FRAME_N_BURSTS": str(static.ARQ_RX_FRAME_N_BURSTS),
                        "ARQ_RX_N_CURRENT_ARQ_FRAME": str(static.ARQ_RX_N_CURRENT_ARQ_FRAME),
                        "ARQ_N_ARQ_FRAMES_PER_DATA_FRAME": str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME),
                        "ARQ_BYTES_PER_MINUTE" : str(static.ARQ_BYTES_PER_MINUTE),
                        "ARQ_TRANSMISSION_PERCENT" : str(static.ARQ_TRANSMISSION_PERCENT),
                        "TOTAL_BYTES" : str(static.TOTAL_BYTES),
                        
                        "STATIONS" : [],
                        "EOF" : "EOF",
                    }
                    
                    for i in range(0, len(static.HEARD_STATIONS)):
                        output["STATIONS"].append({"DXCALLSIGN": str(static.HEARD_STATIONS[i][0], 'utf-8'),"DXGRID": str(static.HEARD_STATIONS[i][1], 'utf-8'), "TIMESTAMP": static.HEARD_STATIONS[i][2], "DATATYPE": static.HEARD_STATIONS[i][3], "SNR": static.HEARD_STATIONS[i][4]})  
                    
                    
                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))



                if received_json["type"] == 'GET' and received_json["command"] == 'RX_BUFFER':
                    output = {
                        "COMMAND": "RX_BUFFER",
                        "DATA" : [],
                        "EOF" : "EOF",
                    }
                    for i in range(0, len(static.RX_BUFFER)):
                        #print(static.RX_BUFFER[i])
                        
                        
                        output["DATA"].append({"DXCALLSIGN": str(static.RX_BUFFER[i][0], 'utf-8'),"DXGRID": str(static.RX_BUFFER[i][1], 'utf-8'), "TIMESTAMP": static.RX_BUFFER[i][2], "DATA": static.RX_BUFFER[i][3]})  
                        
                        print(output)
                        jsondata = json.dumps(output)
                        
                        print(jsondata)
                        self.request.sendall(bytes(jsondata, encoding))
                    
                    
                    
                    
                    
                    
                    
                    
                
                    #data = data.split('GET:RX_BUFFER:')
                    #bufferposition = int(data[1]) - 1
                    # print("BUFFER-LENGTH:" + str(len(static.RX_BUFFER)))
                    # bufferposition = 1
                    # if bufferposition == -1:
                    #     if len(static.RX_BUFFER) > 0:
                    #         self.request.sendall(static.RX_BUFFER[-1])
                    #if bufferposition <= len(static.RX_BUFFER) > 0:
                    #    print(static.RX_BUFFER[bufferposition])
                    #    self.request.sendall(bytes(static.RX_BUFFER[bufferposition]))
                        
                        




                if received_json["type"] == 'SET' and received_json["command"] == 'DEL_RX_BUFFER':
                    static.RX_BUFFER = []
            
            #exception, if JSON cant be decoded
            except Exception as e:
                print("############ START OF ERROR #####################")
                print("SOCKET COMMAND ERROR: " + data)
                print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("############ END OF ERROR #######################")                        
        print("Client disconnected...")

def start_cmd_socket():

    try:
        logging.info("SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: " + str(static.PORT))
        socketserver.TCPServer.allow_reuse_address = True  # https://stackoverflow.com/a/16641793
        cmdserver = socketserver.TCPServer((static.HOST, static.PORT), CMDTCPRequestHandler)
        cmdserver.serve_forever()

    finally:
        cmdserver.server_close()
