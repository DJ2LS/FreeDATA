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
import ujson as json
#import json
import asyncio
import time

import static
import data_handler
import helpers

import sys
import os

import logging, structlog, log_handler



class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
    
        structlog.get_logger("structlog").debug("[TNC] Client connected", ip=self.client_address[0])

        # loop through socket buffer until timeout is reached. then close buffer
        socketTimeout = time.time() + 3
        while socketTimeout > time.time():

            time.sleep(0.01)
            encoding = 'utf-8'
            #data = str(self.request.recv(1024), 'utf-8')

            data = bytes()

            # we need to loop through buffer until end of chunk is reached or timeout occured
            while True and socketTimeout > time.time():

                chunk = self.request.recv(71)  # we keep amount of bytes short
                data += chunk
                # or chunk.endswith(b'\n'):
                if chunk.endswith(b'}\n') or chunk.endswith(b'}'):
                    break
            data = data[:-1]  # remove b'\n'
            data = str(data, 'utf-8')

            if len(data) > 0:
                socketTimeout = time.time() + static.SOCKET_TIMEOUT

            # convert data to json object
            # we need to do some error handling in case of socket timeout or decoding issue
            try:
                # only read first line of string. multiple lines will cause an json error
                # this occurs possibly, if we are getting data too fast
                #    data = data.splitlines()[0]
                #    IndexError: list index out of range
                data = data.splitlines()[0]
                received_json = json.loads(data)

            # except ValueError as e:
            #    print("++++++++++++ START OF JSON ERROR +++++++++++++++++++++++")
            #    print(e)
            #    print("-----------------------------------")
            #    print(data)
            #    print("++++++++++++ END OF JSON ERROR +++++++++++++++++++++++++")
            #    received_json = {}
            #    break
            # try:

                # CQ CQ CQ -----------------------------------------------------
                if received_json["command"] == "CQCQCQ":
                    #socketTimeout = 0
                    # asyncio.run(data_handler.transmit_cq())
                    CQ_THREAD = threading.Thread(target=data_handler.transmit_cq, args=[], name="CQ")
                    CQ_THREAD.start()

                # START_BEACON -----------------------------------------------------
                if received_json["command"] == "START_BEACON":
                    static.BEACON_STATE = True
                    interval = int(received_json["parameter"])
                    BEACON_THREAD = threading.Thread(target=data_handler.run_beacon, args=[interval], name="START BEACON")
                    BEACON_THREAD.start()
                    
                # STOP_BEACON -----------------------------------------------------
                if received_json["command"] == "STOP_BEACON":
                    static.BEACON_STATE = False
                    structlog.get_logger("structlog").warning("[TNC] Stopping beacon!")
                    
                                        
                # PING ----------------------------------------------------------
                if received_json["type"] == 'PING' and received_json["command"] == "PING":
                    # send ping frame and wait for ACK
                    dxcallsign = received_json["dxcallsign"]
                    # asyncio.run(data_handler.transmit_ping(dxcallsign))
                    PING_THREAD = threading.Thread(target=data_handler.transmit_ping, args=[dxcallsign], name="PING")
                    PING_THREAD.start()

                # and static.ARQ_READY_FOR_DATA == True: # and static.ARQ_STATE == 'CONNECTED' :
                if received_json["type"] == 'ARQ' and received_json["command"] == "sendFile":
                    static.TNC_STATE = 'BUSY'

                    # on a new transmission we reset the timer
                    static.ARQ_START_OF_TRANSMISSION = int(time.time())

                    dxcallsign = received_json["dxcallsign"]
                    mode = int(received_json["mode"])
                    n_frames = int(received_json["n_frames"])
                    filename = received_json["filename"]
                    filetype = received_json["filetype"]
                    data = received_json["data"]
                    checksum = received_json["checksum"]
                   

                    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(
                        static.DXCALLSIGN)
        
                    # dt = datatype
                    # --> f = file
                    # --> m = message
                    # fn = filename
                    # ft = filetype
                    # d = data                
                    # crc = checksum
                    rawdata = {"dt": "f", "fn": filename, "ft": filetype,"d": data, "crc": checksum}
                    dataframe = json.dumps(rawdata)
                    data_out = bytes(dataframe, 'utf-8')

                    ARQ_DATA_THREAD = threading.Thread(target=data_handler.open_dc_and_transmit, args=[data_out, mode, n_frames], name="ARQ_DATA")
                    ARQ_DATA_THREAD.start()
                    # asyncio.run(data_handler.arq_transmit(data_out))
                # send message
                if received_json["type"] == 'ARQ' and received_json["command"] == "sendMessage":
                    static.TNC_STATE = 'BUSY'
                    print(received_json)
                    # on a new transmission we reset the timer
                    static.ARQ_START_OF_TRANSMISSION = int(time.time())

                    dxcallsign = received_json["dxcallsign"]
                    mode = int(received_json["mode"])
                    n_frames = int(received_json["n_frames"])
                    data = received_json["d"] # d = data
                    checksum = received_json["crc"] # crc = checksum
                   

                    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
                    
                    # dt = datatype
                    # --> f = file
                    # --> m = message
                    # fn = filename
                    # ft = filetype
                    # d = data                
                    # crc = checksum
                    rawdata = {"dt": "m","d": data, "crc": checksum}
                    dataframe = json.dumps(rawdata)
                    data_out = bytes(dataframe, 'utf-8')

                    ARQ_DATA_THREAD = threading.Thread(target=data_handler.open_dc_and_transmit, args=[data_out, mode, n_frames], name="ARQ_DATA")
                    ARQ_DATA_THREAD.start()
                    
                    
                if received_json["type"] == 'ARQ' and received_json["command"] == "stopTransmission":
                    print(" >>> STOPPING TRANSMISSION <<<")
                    structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
                    static.TNC_STATE = 'IDLE'
                    static.ARQ_STATE = 'IDLE'

                    
                # SETTINGS AND STATUS ---------------------------------------------
                if received_json["type"] == 'SET' and received_json["command"] == 'MYCALLSIGN':
                    callsign = received_json["parameter"]

                    if bytes(callsign, encoding) == b'':
                        self.request.sendall(b'INVALID CALLSIGN')
                    else:
                        static.MYCALLSIGN = bytes(callsign, encoding)
                        static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)
  
                        structlog.get_logger("structlog").info("[TNC] SET MYCALL", grid=static.MYCALLSIGN, crc=static.MYCALLSIGN_CRC8)
                
                if received_json["type"] == 'SET' and received_json["command"] == 'MYGRID':
                    mygrid = received_json["parameter"]

                    if bytes(mygrid, encoding) == b'':
                        self.request.sendall(b'INVALID GRID')
                    else:
                        static.MYGRID = bytes(mygrid, encoding)
                        structlog.get_logger("structlog").info("[TNC] SET MYGRID", grid=static.MYGRID)

                if received_json["type"] == 'GET' and received_json["command"] == 'STATION_INFO':
                    output = {
                        "COMMAND": "STATION_INFO",
                        "TIMESTAMP": received_json["timestamp"],
                        "MY_CALLSIGN": str(static.MYCALLSIGN, encoding),
                        "DX_CALLSIGN": str(static.DXCALLSIGN, encoding),
                        "DX_GRID": str(static.DXGRID, encoding),
                        "EOF": "EOF",
                    }

                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))

                if received_json["type"] == 'GET' and received_json["command"] == 'TNC_STATE':

                    output = {
                        "COMMAND": "TNC_STATE",
                        "TIMESTAMP": received_json["timestamp"],
                        "PTT_STATE": str(static.PTT_STATE),
                        #"CHANNEL_STATE": str(static.CHANNEL_STATE),
                        "TNC_STATE": str(static.TNC_STATE),
                        "ARQ_STATE": str(static.ARQ_STATE),
                        "AUDIO_RMS": str(static.AUDIO_RMS),
                        "SNR": str(static.SNR),
                        "FREQUENCY": str(static.HAMLIB_FREQUENCY),
                        "MODE": str(static.HAMLIB_MODE),
                        "BANDWITH": str(static.HAMLIB_BANDWITH),
                        "FFT": str(static.FFT),
                        "SCATTER": static.SCATTER,
                        "RX_BUFFER_LENGTH": str(len(static.RX_BUFFER)),
                        "RX_MSG_BUFFER_LENGTH": str(len(static.RX_MSG_BUFFER)),
                        "ARQ_BYTES_PER_MINUTE": str(static.ARQ_BYTES_PER_MINUTE),
                        "ARQ_BYTES_PER_MINUTE_BURST": str(static.ARQ_BYTES_PER_MINUTE_BURST),
                        "ARQ_TRANSMISSION_PERCENT": str(static.ARQ_TRANSMISSION_PERCENT),
                        "TOTAL_BYTES": str(static.TOTAL_BYTES),
                        "INFO" : static.INFO,
                        "BEACON_STATE" : str(static.BEACON_STATE),
                        "STATIONS": [],
                        "EOF": "EOF",
                    }

                    # we want to transmit scatter data only once to reduce network traffic
                    static.SCATTER = []
                    
                    # we want to display INFO messages only once
                    static.INFO = []

                    # add heard stations to heard stations object
                    for i in range(0, len(static.HEARD_STATIONS)):
                        output["STATIONS"].append({"DXCALLSIGN": str(static.HEARD_STATIONS[i][0], 'utf-8'), "DXGRID": str(static.HEARD_STATIONS[i][1], 'utf-8'),"TIMESTAMP": static.HEARD_STATIONS[i][2], "DATATYPE": static.HEARD_STATIONS[i][3], "SNR": static.HEARD_STATIONS[i][4], "OFFSET": static.HEARD_STATIONS[i][5], "FREQUENCY": static.HEARD_STATIONS[i][6]})

                    try:
                        jsondata = json.dumps(output)
                    except ValueError as e:
                        structlog.get_logger("structlog").error(e, data=jsondata)

                    try:
                        self.request.sendall(bytes(jsondata, encoding))
                    except Exception as e:
                        structlog.get_logger("structlog").error(e, data=jsondata)

                if received_json["type"] == 'GET' and received_json["command"] == 'RX_BUFFER':
                    output = {
                        "COMMAND": "RX_BUFFER",
                        "DATA-ARRAY": [],
                        "EOF": "EOF",
                    }
                    for i in range(0, len(static.RX_BUFFER)):

                        rawdata = json.loads(static.RX_BUFFER[i][3])
                        output["DATA-ARRAY"].append({"DXCALLSIGN": str(static.RX_BUFFER[i][0], 'utf-8'), "DXGRID": str(static.RX_BUFFER[i][1], 'utf-8'), "TIMESTAMP": static.RX_BUFFER[i][2], "RXDATA": [rawdata]})

                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))

                if received_json["type"] == 'GET' and received_json["command"] == 'RX_MSG_BUFFER':
                    output = {
                        "COMMAND": "RX_MSG_BUFFER",
                        "DATA-ARRAY": [],
                        "EOF": "EOF",
                    }
                    for i in range(0, len(static.RX_MSG_BUFFER)):

                        rawdata = json.loads(static.RX_MSG_BUFFER[i][3])
                        output["DATA-ARRAY"].append({"DXCALLSIGN": str(static.RX_MSG_BUFFER[i][0], 'utf-8'), "DXGRID": str(static.RX_MSG_BUFFER[i][1], 'utf-8'), "TIMESTAMP": static.RX_MSG_BUFFER[i][2], "RXDATA": [rawdata]})

                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))
                    
                if received_json["type"] == 'SET' and received_json["command"] == 'DEL_RX_BUFFER':
                    static.RX_BUFFER = []                    
                    
                if received_json["type"] == 'SET' and received_json["command"] == 'DEL_RX_MSG_BUFFER':
                    static.RX_MSG_BUFFER = []

            # exception, if JSON cant be decoded
            # except Exception as e:
            except:
                print("############ START OF ERROR #####################")
                print("SOCKET COMMAND ERROR: " + data)
                e = sys.exc_info()[0]
                print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("############ END OF ERROR #######################")

                print("reset of connection...")
                structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
                #socketTimeout = 0

                structlog.get_logger("structlog").error("[TNC] Network error", e = sys.exc_info()[0])
        structlog.get_logger("structlog").warning("[TNC] Closing client socket") 

        
        
def start_cmd_socket():

    try:
        structlog.get_logger("structlog").info("[TNC] Starting TCP/IP socket", port=static.PORT)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        cmdserver = ThreadedTCPServer(
            (static.HOST, static.PORT), ThreadedTCPRequestHandler)
        server_thread = threading.Thread(target=cmdserver.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    except:
        structlog.get_logger("structlog").error("[TNC] Starting TCP/IP socket failed", port=static.PORT)
        e = sys.exc_info()[0]
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

