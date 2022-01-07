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
import ujson as json
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
    
        structlog.get_logger("structlog").debug("[TNC] Client connected", ip=self.client_address[0], port=self.client_address[1])

        # set encoding
        encoding = 'utf-8'
        
        # loop through socket buffer until timeout is reached. then close buffer
        socketTimeout = time.time() + static.SOCKET_TIMEOUT
        while socketTimeout > time.time():

            time.sleep(0.01)
            
            data = bytes()

            # we need to loop through buffer until end of chunk is reached or timeout occured
            while socketTimeout > time.time():

                chunk = self.request.recv(71)  # we keep amount of bytes short
                data += chunk

                if chunk.startswith(b'{"type"') and chunk.endswith(b'}\n'):
                    break
                    
            data = data[:-1]  # remove b'\n'
            data = str(data, encoding)

            if len(data) > 0:
                # reset socket timeout
                socketTimeout = time.time() + static.SOCKET_TIMEOUT
                # only read first line of string. multiple lines will cause an json error
                # this occurs possibly, if we are getting data too fast
                #    data = data.splitlines()[0]
                data = data.splitlines()[0]


            # we need to do some error handling in case of socket timeout or decoding issue
            try:

                # convert data to json object
                received_json = json.loads(data)

                # CQ CQ CQ -----------------------------------------------------
                if received_json["command"] == "CQCQCQ":
                    data_handler.DATA_QUEUE_TRANSMIT.put(['CQ'])

                # START_BEACON -----------------------------------------------------
                if received_json["command"] == "START_BEACON":

                    static.BEACON_STATE = True
                    interval = int(received_json["parameter"])
                    data_handler.DATA_QUEUE_TRANSMIT.put(['BEACON', interval, True])

                    
                # STOP_BEACON -----------------------------------------------------
                if received_json["command"] == "STOP_BEACON":
                    static.BEACON_STATE = False
                    structlog.get_logger("structlog").warning("[TNC] Stopping beacon!")
                    data_handler.DATA_QUEUE_TRANSMIT.put(['BEACON', interval, False])
                    
                                        
                # PING ----------------------------------------------------------
                if received_json["type"] == 'PING' and received_json["command"] == "PING":
                    # send ping frame and wait for ACK
                    dxcallsign = received_json["dxcallsign"]
                    data_handler.DATA_QUEUE_TRANSMIT.put(['PING', dxcallsign])



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
                    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
        
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
                    data_handler.DATA_QUEUE_TRANSMIT.put(['ARQ_FILE', data_out, mode, n_frames])

                # send message
                if received_json["type"] == 'ARQ' and received_json["command"] == "sendMessage":
                    static.TNC_STATE = 'BUSY'
                    print(received_json)
                    # on a new transmission we reset the timer
                    static.ARQ_START_OF_TRANSMISSION = int(time.time())

                    dxcallsign = received_json["dxcallsign"]
                    mode = int(received_json["mode"])
                    n_frames = int(received_json["n_frames"])
                    data = received_json["data"] # d = data
                    checksum = received_json["checksum"] # crc = checksum
                   

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

                    data_handler.DATA_QUEUE_TRANSMIT.put(['ARQ_MESSAGE', data_out, mode, n_frames])

                    
                    
                if received_json["type"] == 'ARQ' and received_json["command"] == "stopTransmission":
                    print(" >>> STOPPING TRANSMISSION <<<")
                    structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
                    static.TNC_STATE = 'IDLE'
                    static.ARQ_STATE = False

  

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
                        "ARQ_COMPRESSION_FACTOR": str(static.ARQ_COMPRESSION_FACTOR),
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
            except Exception as e:
                #socketTimeout = 0
                structlog.get_logger("structlog").error("[TNC] Network error", e=e)
        structlog.get_logger("structlog").warning("[TNC] Closing client socket", ip=self.client_address[0], port=self.client_address[1]) 

