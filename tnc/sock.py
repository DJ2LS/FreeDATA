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
import queue
import psutil
import audio
import base64

SOCKET_QUEUE = queue.Queue()
DAEMON_QUEUE = queue.Queue()

CONNECTED_CLIENTS = set()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
                
                
                
class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):

        
    def send_to_client(self):
        tempdata = b''
        while self.connection_alive:
            # send tnc state as network stream
            # check server port against daemon port and send corresponding data
            
            if self.server.server_address[1] == static.PORT and not static.TNCSTARTED:
                data = send_tnc_state()
                if data != tempdata:
                    tempdata = data
                    SOCKET_QUEUE.put(data)
            else:
                data = send_daemon_state()
                if data != tempdata:
                    tempdata = data
                    SOCKET_QUEUE.put(data)
                time.sleep(0.5)
            

            while not SOCKET_QUEUE.empty():
                data = SOCKET_QUEUE.get()
                sock_data = bytes(data, 'utf-8')
                sock_data += b'\n' # append line limiter
                # send data to all clients
                try:
                    for client in CONNECTED_CLIENTS:
                        try:
                            client.send(sock_data)
                        except:
                            print("connection lost...")
                            CONNECTED_CLIENTS.remove(self.request)
                except:
                    print("client not anymore in client list")
                    
            # we want to transmit scatter data only once to reduce network traffic
            static.SCATTER = []
            # we want to display INFO messages only once
            static.INFO = []            
            #self.request.sendall(sock_data)
            time.sleep(0.15)

    def receive_from_client(self):
        data = bytes()
        while self.connection_alive:
            # BrokenPipeError: [Errno 32] Broken pipe
            chunk = self.request.recv(1024)
            data += chunk
            
            if chunk == b'':
                #print("connection broken. Closing...")
                self.connection_alive = False
                
            if data.startswith(b'{') and data.endswith(b'}\n'):                
                # split data by \n if we have multiple commands in socket buffer
                data = data.split(b'\n')
                # remove empty data
                data.remove(b'')
                
                # iterate thorugh data list
                for commands in data:
                    if self.server.server_address[1] == static.PORT:
                        process_tnc_commands(commands)
                    else:
                        process_daemon_commands(commands)
                
                # finally delete our rx buffer to be ready for new commands
                data = bytes()

 
    def handle(self):
        CONNECTED_CLIENTS.add(self.request)

        structlog.get_logger("structlog").debug("[TNC] Client connected", ip=self.client_address[0], port=self.client_address[1])
        self.connection_alive = True
        
        self.sendThread = threading.Thread(target=self.send_to_client, args=[]).start()
        self.receiveThread = threading.Thread(target=self.receive_from_client, args=[]).start()
        
        # keep connection alive until we close it
        while self.connection_alive:
            time.sleep(1)

        

    def finish(self):
        structlog.get_logger("structlog").warning("[TNC] Closing client socket", ip=self.client_address[0], port=self.client_address[1]) 
        try:
            CONNECTED_CLIENTS.remove(self.request)
        except:
            print("client connection already removed from client list")


def process_tnc_commands(data):
    # we need to do some error handling in case of socket timeout or decoding issue
    try:

        # convert data to json object
        received_json = json.loads(data)
        # CQ CQ CQ -----------------------------------------------------
        if received_json["command"] == "cqcqcq":
            try:
                data_handler.DATA_QUEUE_TRANSMIT.put(['CQ'])
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
        # START_BEACON -----------------------------------------------------
        if received_json["command"] == "start_beacon":
            try:
                static.BEACON_STATE = True
                interval = int(received_json["parameter"])
                data_handler.DATA_QUEUE_TRANSMIT.put(['BEACON', interval, True])
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
                
        # STOP_BEACON -----------------------------------------------------
        if received_json["command"] == "stop_beacon":
            try:
                static.BEACON_STATE = False
                structlog.get_logger("structlog").warning("[TNC] Stopping beacon!")
                data_handler.DATA_QUEUE_TRANSMIT.put(['BEACON', None, False])
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
                                
        # PING ----------------------------------------------------------
        if received_json["type"] == 'ping' and received_json["command"] == "ping":
            # send ping frame and wait for ACK
            try:
                dxcallsign = received_json["dxcallsign"]
                data_handler.DATA_QUEUE_TRANSMIT.put(['PING', dxcallsign])
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
        # TRANSMIT RAW DATA -------------------------------------------
        if received_json["type"] == 'arq' and received_json["command"] == "send_raw":
            try:    
                dxcallsign = received_json["parameter"][0]["dxcallsign"]
                mode = int(received_json["parameter"][0]["mode"])
                n_frames = int(received_json["parameter"][0]["n_frames"])
                base64data = received_json["parameter"][0]["data"]
                
                if not len(base64data) % 4: 
                    binarydata = base64.b64decode(base64data)

                    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                    static.DXCALLSIGN_CRC = helpers.get_crc_16(static.DXCALLSIGN)
                    data_handler.DATA_QUEUE_TRANSMIT.put(['ARQ_RAW', binarydata, mode, n_frames])

                else:
                    raise TypeError
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
                    

        
        # STOP TRANSMISSION ----------------------------------------------------------    
        if received_json["type"] == 'arq' and received_json["command"] == "stop_transmission":
            try:
                if static.TNC_STATE == 'BUSY' or static.ARQ_STATE:
                    data_handler.DATA_QUEUE_TRANSMIT.put(['STOP'])
                structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
                static.TNC_STATE = 'IDLE'
                static.ARQ_STATE = False
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
                

        if received_json["type"] == 'get' and received_json["command"] == 'rx_buffer':
            try:
                output = {
                    "command": "rx_buffer",
                    "data-array": [],
                }
                
                for i in range(0, len(static.RX_BUFFER)):
                    print(static.RX_BUFFER[i][4])
                    #rawdata = json.loads(static.RX_BUFFER[i][4])
                    base64_data = static.RX_BUFFER[i][4]
                    output["data-array"].append({"uuid": static.RX_BUFFER[i][0],"timestamp": static.RX_BUFFER[i][1], "dxcallsign": str(static.RX_BUFFER[i][2], 'utf-8'), "dxgrid": str(static.RX_BUFFER[i][3], 'utf-8'),  "data": base64_data})

                jsondata = json.dumps(output)
                #self.request.sendall(bytes(jsondata, encoding))
                SOCKET_QUEUE.put(jsondata)
                
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
                
    
        if received_json["type"] == 'set' and received_json["command"] == 'del_rx_buffer':
            try:
                static.RX_BUFFER = []
            except Exception as e:        
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

    # exception, if JSON cant be decoded
    except Exception as e:
        structlog.get_logger("structlog").error("[TNC] JSON decoding error", e=e)

def send_tnc_state():
    
    encoding = 'utf-8'

    output = {
        "command": "tnc_state",
        "ptt_state": str(static.PTT_STATE),
        "tnc_state": str(static.TNC_STATE),
        "arq_state": str(static.ARQ_STATE),
        "audio_rms": str(static.AUDIO_RMS),
        "snr": str(static.SNR),
        "frequency": str(static.HAMLIB_FREQUENCY),
        "mode": str(static.HAMLIB_MODE),
        "bandwith": str(static.HAMLIB_BANDWITH),
        "fft": str(static.FFT),
        "scatter": static.SCATTER,
        "rx_buffer_length": str(len(static.RX_BUFFER)),
        "rx_msg_buffer_length": str(len(static.RX_MSG_BUFFER)),
        "arq_bytes_per_minute": str(static.ARQ_BYTES_PER_MINUTE),
        "arq_bytes_per_minute_burst": str(static.ARQ_BYTES_PER_MINUTE_BURST),
        "arq_compression_factor": str(static.ARQ_COMPRESSION_FACTOR),
        "arq_transmission_percent": str(static.ARQ_TRANSMISSION_PERCENT),
        "total_bytes": str(static.TOTAL_BYTES),
        "info" : static.INFO,
        "beacon_state" : str(static.BEACON_STATE),
        "stations": [],
        "mycallsign": str(static.MYCALLSIGN, encoding),
        "dxcallsign": str(static.DXCALLSIGN, encoding),
        "dxgrid": str(static.DXGRID, encoding),
    }

    # add heard stations to heard stations object
    for i in range(0, len(static.HEARD_STATIONS)):
        output["stations"].append({"dxcallsign": str(static.HEARD_STATIONS[i][0], 'utf-8'), "dxgrid": str(static.HEARD_STATIONS[i][1], 'utf-8'),"timestamp": static.HEARD_STATIONS[i][2], "datatype": static.HEARD_STATIONS[i][3], "snr": static.HEARD_STATIONS[i][4], "offset": static.HEARD_STATIONS[i][5], "frequency": static.HEARD_STATIONS[i][6]})
      
    jsondata = json.dumps(output)
    return jsondata


def process_daemon_commands(data):
    # convert data to json object
    received_json = json.loads(data)
    
    if received_json["type"] == 'set' and received_json["command"] == 'mycallsign':
        try:
            callsign = received_json["parameter"]
            print(received_json)
            if bytes(callsign, 'utf-8') == b'':
                self.request.sendall(b'INVALID CALLSIGN')
                structlog.get_logger("structlog").warning("[DMN] SET MYCALL FAILED", call=static.MYCALLSIGN, crc=static.MYCALLSIGN_CRC)
            else:
                static.MYCALLSIGN = bytes(callsign, 'utf-8')
                static.MYCALLSIGN_CRC = helpers.get_crc_16(static.MYCALLSIGN)

                structlog.get_logger("structlog").info("[DMN] SET MYCALL", call=static.MYCALLSIGN, crc=static.MYCALLSIGN_CRC)
        except Exception as e:        
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
            
            
    if received_json["type"] == 'set' and received_json["command"] == 'mygrid':
        try:
            mygrid = received_json["parameter"]

            if bytes(mygrid, 'utf-8') == b'':
                self.request.sendall(b'INVALID GRID')
            else:
                static.MYGRID = bytes(mygrid, 'utf-8')
                structlog.get_logger("structlog").info("[SCK] SET MYGRID", grid=static.MYGRID)
        except Exception as e:        
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
            
            
    if received_json["type"] == 'set' and received_json["command"] == 'start_tnc' and not static.TNCSTARTED:
        
        try:
            mycall = str(received_json["parameter"][0]["mycall"])
            mygrid = str(received_json["parameter"][0]["mygrid"])
            rx_audio = str(received_json["parameter"][0]["rx_audio"])
            tx_audio = str(received_json["parameter"][0]["tx_audio"])
            devicename = str(received_json["parameter"][0]["devicename"])
            deviceport = str(received_json["parameter"][0]["deviceport"])
            serialspeed = str(received_json["parameter"][0]["serialspeed"])
            pttprotocol = str(received_json["parameter"][0]["pttprotocol"])
            pttport = str(received_json["parameter"][0]["pttport"])
            data_bits = str(received_json["parameter"][0]["data_bits"])
            stop_bits = str(received_json["parameter"][0]["stop_bits"])
            handshake = str(received_json["parameter"][0]["handshake"])
            radiocontrol = str(received_json["parameter"][0]["radiocontrol"])
            rigctld_ip = str(received_json["parameter"][0]["rigctld_ip"])
            rigctld_port = str(received_json["parameter"][0]["rigctld_port"])
            enable_scatter = str(received_json["parameter"][0]["enable_scatter"])
            enable_fft = str(received_json["parameter"][0]["enable_fft"])
            low_bandwith_mode = str(received_json["parameter"][0]["low_bandwith_mode"])

            DAEMON_QUEUE.put(['STARTTNC', \
                                    mycall, \
                                    mygrid, \
                                    rx_audio, \
                                    tx_audio, \
                                    devicename, \
                                    deviceport, \
                                    serialspeed, \
                                    pttprotocol, \
                                    pttport, \
                                    data_bits, \
                                    stop_bits, \
                                    handshake, \
                                    radiocontrol, \
                                    rigctld_ip, \
                                    rigctld_port, \
                                    enable_scatter, \
                                    enable_fft, \
                                    low_bandwith_mode \
                                    ])
            
        except Exception as e:        
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

    if received_json["type"] == 'get' and received_json["command"] == 'test_hamlib':

        try:
            devicename = str(received_json["parameter"][0]["devicename"])
            deviceport = str(received_json["parameter"][0]["deviceport"])
            serialspeed = str(received_json["parameter"][0]["serialspeed"])
            pttprotocol = str(received_json["parameter"][0]["pttprotocol"])
            pttport = str(received_json["parameter"][0]["pttport"])
            data_bits = str(received_json["parameter"][0]["data_bits"])
            stop_bits = str(received_json["parameter"][0]["stop_bits"])
            handshake = str(received_json["parameter"][0]["handshake"])
            radiocontrol = str(received_json["parameter"][0]["radiocontrol"])
            rigctld_ip = str(received_json["parameter"][0]["rigctld_ip"])
            rigctld_port = str(received_json["parameter"][0]["rigctld_port"])

            DAEMON_QUEUE.put(['TEST_HAMLIB', \
                                    devicename, \
                                    deviceport, \
                                    serialspeed, \
                                    pttprotocol, \
                                    pttport, \
                                    data_bits, \
                                    stop_bits, \
                                    handshake, \
                                    radiocontrol, \
                                    rigctld_ip, \
                                    rigctld_port \
                                    ])
        except Exception as e:        
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
            
    if received_json["type"] == 'set' and received_json["command"] == 'stop_tnc':
        try:
            static.TNCPROCESS.kill()
            structlog.get_logger("structlog").warning("[DMN] Stopping TNC")
            static.TNCSTARTED = False
        except Exception as e:        
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)
            
def send_daemon_state():
    
    python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])

    output = {
        'command': 'daemon_state',
        'daemon_state': [],
        'python_version': str(python_version),
        'hamlib_version': static.HAMLIB_VERSION,
        'input_devices': static.AUDIO_INPUT_DEVICES,
        'output_devices': static.AUDIO_OUTPUT_DEVICES,
        'serial_devices': static.SERIAL_DEVICES,
        #'cpu': str(psutil.cpu_percent()),
        #'ram': str(psutil.virtual_memory().percent),
        'version': '0.1'
        }
    
    if static.TNCSTARTED:
        output["daemon_state"].append({"status": "running"})
    else:
        output["daemon_state"].append({"status": "stopped"})
        
    jsondata = json.dumps(output)
    return jsondata