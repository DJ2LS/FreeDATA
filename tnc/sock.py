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
import atexit
import base64

import queue
import socketserver
import sys
import threading
import time

import structlog
import ujson as json

import data_handler
import helpers

import static

SOCKET_QUEUE = queue.Queue()
DAEMON_QUEUE = queue.Queue()

CONNECTED_CLIENTS = set()
CLOSE_SIGNAL = False


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    the socket handler base class
    """
    pass


class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    """ """
    connection_alive = False

    def send_to_client(self):
        """
        function called by socket handler
        send data to a network client if available
        """
        tempdata = b''
        while self.connection_alive and not CLOSE_SIGNAL:
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
                sock_data += b'\n'  # append line limiter

                # send data to all clients
                # try:
                for client in CONNECTED_CLIENTS:
                    try:
                        client.send(sock_data)
                    except Exception as e:
                        # print("connection lost...")
                        structlog.get_logger("structlog").info("[SCK] Connection lost", e=e)
                        self.connection_alive = False

            # we want to transmit scatter data only once to reduce network traffic
            static.SCATTER = []
            # we want to display INFO messages only once
            static.INFO = []
            # self.request.sendall(sock_data)
            time.sleep(0.15)

    def receive_from_client(self):
        """
        function which is called by the socket handler
        it processes the data which is returned by a client
        """
        data = bytes()
        while self.connection_alive and not CLOSE_SIGNAL:
            try:
                chunk = self.request.recv(1024)
                data += chunk

                if chunk == b'':
                    # print("connection broken. Closing...")
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

                        # wait some time between processing multiple commands
                        # this is only a first test to avoid doubled transmission
                        # we might improve this by only processing one command or
                        # doing some kind of selection to determin which commands need to be dropped
                        # and which one can be processed during a running transmission
                        time.sleep(3)

                    # finally delete our rx buffer to be ready for new commands
                    data = bytes()
            except Exception as e:
                structlog.get_logger("structlog").info("[SCK] Connection closed", ip=self.client_address[0],
                                                       port=self.client_address[1], e=e)
                self.connection_alive = False

    def handle(self):
        """
        socket handler
        """
        CONNECTED_CLIENTS.add(self.request)

        structlog.get_logger("structlog").debug("[SCK] Client connected", ip=self.client_address[0],
                                                port=self.client_address[1])
        self.connection_alive = True

        self.sendThread = threading.Thread(target=self.send_to_client, args=[], daemon=True).start()
        self.receiveThread = threading.Thread(target=self.receive_from_client, args=[], daemon=True).start()

        # keep connection alive until we close it
        while self.connection_alive and not CLOSE_SIGNAL:
            time.sleep(1)

    def finish(self):
        """ """
        structlog.get_logger("structlog").warning("[SCK] Closing client socket", ip=self.client_address[0],
                                                  port=self.client_address[1])
        try:
            CONNECTED_CLIENTS.remove(self.request)
        except Exception as e:
            structlog.get_logger("structlog").warning("[SCK] client connection already removed from client list",
                                                      client=self.request, e=e)


def process_tnc_commands(data):
    """
    process tnc commands

    Args:
      data:

    Returns:

    """
    # we need to do some error handling in case of socket timeout or decoding issue
    try:
        # convert data to json object
        received_json = json.loads(data)
        structlog.get_logger("structlog").debug("[SCK] CMD", command=received_json)
        # SET TX AUDIO LEVEL  -----------------------------------------------------
        if received_json["type"] == "set" and received_json["command"] == "tx_audio_level":
            try:
                static.TX_AUDIO_LEVEL = int(received_json["value"])
                command_response("tx_audio_level", True)

            except Exception as e:
                command_response("tx_audio_level", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # TRANSMIT SINE WAVE  -----------------------------------------------------
        if received_json["type"] == "set" and received_json["command"] == "send_test_frame":
            try:
                data_handler.DATA_QUEUE_TRANSMIT.put(['SEND_TEST_FRAME'])
                command_response("send_test_frame", True)
            except Exception as e:
                command_response("send_test_frame", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # CQ CQ CQ -----------------------------------------------------
        if received_json["command"] == "cqcqcq":
            try:
                data_handler.DATA_QUEUE_TRANSMIT.put(['CQ'])
                command_response("cqcqcq", True)

            except Exception as e:
                command_response("cqcqcq", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # START_BEACON -----------------------------------------------------
        if received_json["command"] == "start_beacon":
            try:
                static.BEACON_STATE = True
                interval = int(received_json["parameter"])
                data_handler.DATA_QUEUE_TRANSMIT.put(['BEACON', interval, True])
                command_response("start_beacon", True)
            except Exception as e:
                command_response("start_beacon", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # STOP_BEACON -----------------------------------------------------
        if received_json["command"] == "stop_beacon":
            try:
                structlog.get_logger("structlog").warning("[TNC] Stopping beacon!")
                static.BEACON_STATE = False
                data_handler.DATA_QUEUE_TRANSMIT.put(['BEACON', None, False])
                command_response("stop_beacon", True)
            except Exception as e:
                command_response("stop_beacon", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # PING ----------------------------------------------------------
        if received_json["type"] == 'ping' and received_json["command"] == "ping":
            # send ping frame and wait for ACK
            try:
                dxcallsign = received_json["dxcallsign"]

                # additional step for beeing sure our callsign is correctly
                # in case we are not getting a station ssid
                # then we are forcing a station ssid = 0
                dxcallsign = helpers.callsign_to_bytes(dxcallsign)
                dxcallsign = helpers.bytes_to_callsign(dxcallsign)

                data_handler.DATA_QUEUE_TRANSMIT.put(['PING', dxcallsign])
                command_response("ping", True)
            except Exception as e:
                command_response("ping", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # CONNECT ----------------------------------------------------------
        if received_json["type"] == 'arq' and received_json["command"] == "connect":
            static.BEACON_PAUSE = True
            # send ping frame and wait for ACK
            try:
                dxcallsign = received_json["dxcallsign"]

                # additional step for beeing sure our callsign is correctly
                # in case we are not getting a station ssid
                # then we are forcing a station ssid = 0
                dxcallsign = helpers.callsign_to_bytes(dxcallsign)
                dxcallsign = helpers.bytes_to_callsign(dxcallsign)

                static.DXCALLSIGN = dxcallsign
                static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)

                data_handler.DATA_QUEUE_TRANSMIT.put(['CONNECT', dxcallsign])
                command_response("connect", True)
            except Exception as e:
                command_response("connect", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # DISCONNECT ----------------------------------------------------------
        if received_json["type"] == 'arq' and received_json["command"] == "disconnect":
            # send ping frame and wait for ACK
            try:
                data_handler.DATA_QUEUE_TRANSMIT.put(['DISCONNECT'])
                command_response("disconnect", True)
            except Exception as e:
                command_response("disconnect", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # TRANSMIT RAW DATA -------------------------------------------
        if received_json["type"] == 'arq' and received_json["command"] == "send_raw":
            static.BEACON_PAUSE = True
            try:
                if not static.ARQ_SESSION:
                    dxcallsign = received_json["parameter"][0]["dxcallsign"]
                    # additional step for beeing sure our callsign is correctly
                    # in case we are not getting a station ssid
                    # then we are forcing a station ssid = 0
                    dxcallsign = helpers.callsign_to_bytes(dxcallsign)
                    dxcallsign = helpers.bytes_to_callsign(dxcallsign)
                    static.DXCALLSIGN = dxcallsign
                    static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)
                    command_response("send_raw", True)
                else:
                    dxcallsign = static.DXCALLSIGN
                    static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)

                mode = int(received_json["parameter"][0]["mode"])
                n_frames = int(received_json["parameter"][0]["n_frames"])
                base64data = received_json["parameter"][0]["data"]

                # check if specific callsign is set with different SSID than the TNC is initialized
                try:
                    mycallsign = received_json["parameter"][0]["mycallsign"]
                except Exception:
                    mycallsign = static.MYCALLSIGN

                # check if transmission uuid provided else set no-uuid
                try:
                    arq_uuid = received_json["uuid"]
                except Exception:
                    arq_uuid = 'no-uuid'

                if not len(base64data) % 4:
                    binarydata = base64.b64decode(base64data)

                    data_handler.DATA_QUEUE_TRANSMIT.put(['ARQ_RAW', binarydata, mode, n_frames, arq_uuid, mycallsign])
                else:
                    raise TypeError
            except Exception as e:
                command_response("send_raw", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        # STOP TRANSMISSION ----------------------------------------------------------
        if received_json["type"] == 'arq' and received_json["command"] == "stop_transmission":
            try:
                if static.TNC_STATE == 'BUSY' or static.ARQ_STATE:
                    data_handler.DATA_QUEUE_TRANSMIT.put(['STOP'])
                structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
                static.TNC_STATE = 'IDLE'
                static.ARQ_STATE = False
                command_response("stop_transmission", True)
            except Exception as e:
                command_response("stop_transmission", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        if received_json["type"] == 'get' and received_json["command"] == 'rx_buffer':
            try:
                output = {
                    "command": "rx_buffer",
                    "data-array": [],
                }

                for i in range(len(static.RX_BUFFER)):
                    # print(static.RX_BUFFER[i][4])
                    # rawdata = json.loads(static.RX_BUFFER[i][4])
                    base64_data = static.RX_BUFFER[i][4]
                    output["data-array"].append({"uuid": static.RX_BUFFER[i][0], "timestamp": static.RX_BUFFER[i][1],
                                                 "dxcallsign": str(static.RX_BUFFER[i][2], 'utf-8'),
                                                 "dxgrid": str(static.RX_BUFFER[i][3], 'utf-8'), "data": base64_data})

                jsondata = json.dumps(output)
                # self.request.sendall(bytes(jsondata, encoding))
                SOCKET_QUEUE.put(jsondata)
                command_response("rx_buffer", True)

            except Exception as e:
                command_response("rx_buffer", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

        if received_json["type"] == 'set' and received_json["command"] == 'del_rx_buffer':
            try:
                static.RX_BUFFER = []
                command_response("del_rx_buffer", True)
            except Exception as e:
                command_response("del_rx_buffer", False)
                structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

    # exception, if JSON can't be decoded
    except Exception as e:
        structlog.get_logger("structlog").error("[TNC] JSON decoding error", e=e)


def send_tnc_state():
    """
    send the tnc state to network
    """
    encoding = 'utf-8'

    output = {
        "command": "tnc_state",
        "ptt_state": str(static.PTT_STATE),
        "tnc_state": str(static.TNC_STATE),
        "arq_state": str(static.ARQ_STATE),
        "arq_session": str(static.ARQ_SESSION),
        "arq_session_state": str(static.ARQ_SESSION_STATE),
        "audio_rms": str(static.AUDIO_RMS),
        "snr": str(static.SNR),
        "frequency": str(static.HAMLIB_FREQUENCY),
        "speed_level": str(static.ARQ_SPEED_LEVEL),
        "mode": str(static.HAMLIB_MODE),
        "bandwith": str(static.HAMLIB_BANDWITH),
        "fft": str(static.FFT),
        "channel_busy": str(static.CHANNEL_BUSY),
        "scatter": static.SCATTER,
        "rx_buffer_length": str(len(static.RX_BUFFER)),
        "rx_msg_buffer_length": str(len(static.RX_MSG_BUFFER)),
        "arq_bytes_per_minute": str(static.ARQ_BYTES_PER_MINUTE),
        "arq_bytes_per_minute_burst": str(static.ARQ_BYTES_PER_MINUTE_BURST),
        "arq_compression_factor": str(static.ARQ_COMPRESSION_FACTOR),
        "arq_transmission_percent": str(static.ARQ_TRANSMISSION_PERCENT),
        "total_bytes": str(static.TOTAL_BYTES),
        "info": static.INFO,
        "beacon_state": str(static.BEACON_STATE),
        "stations": [],
        "mycallsign": str(static.MYCALLSIGN, encoding),
        "dxcallsign": str(static.DXCALLSIGN, encoding),
        "dxgrid": str(static.DXGRID, encoding),
    }

    # add heard stations to heard stations object
    for heard in static.HEARD_STATIONS:
        output["stations"].append({
            "dxcallsign": str(heard[0], 'utf-8'),
            "dxgrid": str(heard[1], 'utf-8'),
            "timestamp": heard[2],
            "datatype": heard[3],
            "snr": heard[4],
            "offset": heard[5],
            "frequency": heard[6]})

    return json.dumps(output)


def process_daemon_commands(data):
    """
    process daemon commands

    Args:
      data:

    Returns:

    """
    # convert data to json object
    received_json = json.loads(data)
    structlog.get_logger("structlog").debug("[SCK] CMD", command=received_json)
    if received_json["type"] == 'set' and received_json["command"] == 'mycallsign':
        try:
            callsign = received_json["parameter"]

            if bytes(callsign, 'utf-8') == b'':
                self.request.sendall(b'INVALID CALLSIGN')
                structlog.get_logger("structlog").warning("[DMN] SET MYCALL FAILED", call=static.MYCALLSIGN,
                                                          crc=static.MYCALLSIGN_CRC)
            else:
                static.MYCALLSIGN = bytes(callsign, 'utf-8')
                static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)

                command_response("mycallsign", True)
                structlog.get_logger("structlog").info("[DMN] SET MYCALL", call=static.MYCALLSIGN,
                                                       crc=static.MYCALLSIGN_CRC)
        except Exception as e:
            command_response("mycallsign", False)
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

    if received_json["type"] == 'set' and received_json["command"] == 'mygrid':
        try:
            mygrid = received_json["parameter"]

            if bytes(mygrid, 'utf-8') == b'':
                self.request.sendall(b'INVALID GRID')
            else:
                static.MYGRID = bytes(mygrid, 'utf-8')
                structlog.get_logger("structlog").info("[SCK] SET MYGRID", grid=static.MYGRID)
                command_response("mygrid", True)
        except Exception as e:
            command_response("mygrid", False)
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
            enable_fsk = str(received_json["parameter"][0]["enable_fsk"])
            low_bandwith_mode = str(received_json["parameter"][0]["low_bandwith_mode"])
            tuning_range_fmin = str(received_json["parameter"][0]["tuning_range_fmin"])
            tuning_range_fmax = str(received_json["parameter"][0]["tuning_range_fmax"])
            tx_audio_level = str(received_json["parameter"][0]["tx_audio_level"])
            respond_to_cq = str(received_json["parameter"][0]["respond_to_cq"])

            # print some debugging parameters
            for item in received_json["parameter"][0]:
                structlog.get_logger("structlog").debug(f"[DMN] TNC Startup Config : {item}", value=received_json["parameter"][0][item])


            DAEMON_QUEUE.put(['STARTTNC',
                              mycall,
                              mygrid,
                              rx_audio,
                              tx_audio,
                              devicename,
                              deviceport,
                              serialspeed,
                              pttprotocol,
                              pttport,
                              data_bits,
                              stop_bits,
                              handshake,
                              radiocontrol,
                              rigctld_ip,
                              rigctld_port,
                              enable_scatter,
                              enable_fft,
                              low_bandwith_mode,
                              tuning_range_fmin,
                              tuning_range_fmax,
                              enable_fsk,
                              tx_audio_level,
                              respond_to_cq,
                              ])
            command_response("start_tnc", True)

        except Exception as e:
            command_response("start_tnc", False)
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

            DAEMON_QUEUE.put(['TEST_HAMLIB',
                              devicename,
                              deviceport,
                              serialspeed,
                              pttprotocol,
                              pttport,
                              data_bits,
                              stop_bits,
                              handshake,
                              radiocontrol,
                              rigctld_ip,
                              rigctld_port,
                              ])
            command_response("test_hamlib", True)
        except Exception as e:
            command_response("test_hamlib", False)
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)

    if received_json["type"] == 'set' and received_json["command"] == 'stop_tnc':
        try:
            static.TNCPROCESS.kill()
            # unregister process from atexit to avoid process zombies
            atexit.unregister(static.TNCPROCESS.kill)

            structlog.get_logger("structlog").warning("[DMN] Stopping TNC")
            static.TNCSTARTED = False
            command_response("stop_tnc", True)
        except Exception as e:
            command_response("stop_tnc", False)
            structlog.get_logger("structlog").warning("[SCK] command execution error", e=e, command=received_json)


def send_daemon_state():
    """
    send the daemon state to network
    """
    try:
        python_version = f"{str(sys.version_info[0])}.{str(sys.version_info[1])}"

        output = {
            'command': 'daemon_state',
            'daemon_state': [],
            'python_version': str(python_version),
            'hamlib_version': static.HAMLIB_VERSION,
            'input_devices': static.AUDIO_INPUT_DEVICES,
            'output_devices': static.AUDIO_OUTPUT_DEVICES,
            'serial_devices': static.SERIAL_DEVICES,
            # 'cpu': str(psutil.cpu_percent()),
            # 'ram': str(psutil.virtual_memory().percent),
            'version': '0.1'
        }

        if static.TNCSTARTED:
            output["daemon_state"].append({"status": "running"})
        else:
            output["daemon_state"].append({"status": "stopped"})

        return json.dumps(output)

    except Exception as e:
        structlog.get_logger("structlog").warning("[SCK] error", e=e)
        return None


def command_response(command, status):
    s_status = "OK" if status else "Failed"
    jsondata = {"command_response": command, "status": s_status}
    data_out = json.dumps(jsondata)
    SOCKET_QUEUE.put(data_out)
