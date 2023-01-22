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
import wave

import helpers
import static
import structlog
import ujson as json
from exceptions import NoCallsign
from queues import DATA_QUEUE_TRANSMIT, RX_BUFFER, RIGCTLD_COMMAND_QUEUE

SOCKET_QUEUE = queue.Queue()
DAEMON_QUEUE = queue.Queue()

CONNECTED_CLIENTS = set()
CLOSE_SIGNAL = False

log = structlog.get_logger("sock")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    the socket handler base class
    """

    pass


class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    """ """

    connection_alive = False

    connection_alive = False
    log = structlog.get_logger("ThreadedTCPRequestHandler")

    def send_to_client(self):
        """
        function called by socket handler
        send data to a network client if available
        """
        tempdata = b""
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
                threading.Event().wait(0.5)

            while not SOCKET_QUEUE.empty():
                data = SOCKET_QUEUE.get()
                sock_data = bytes(data, "utf-8")
                sock_data += b"\n"  # append line limiter

                # send data to all clients
                try:
                    for client in CONNECTED_CLIENTS:
                        try:
                            client.send(sock_data)
                        except Exception as err:
                            self.log.info("[SCK] Connection lost", e=err)
                            # TODO: Check if we really should set connection alive to false. This might disconnect all other clients as well...
                            self.connection_alive = False
                except Exception as err:
                    self.log.debug("[SCK] catch harmless RuntimeError: Set changed size during iteration", e=err)

            # we want to transmit scatter data only once to reduce network traffic
            static.SCATTER = []
            # we want to display INFO messages only once
            static.INFO = []
            # self.request.sendall(sock_data)
            threading.Event().wait(0.15)

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

                if chunk == b"":
                    # print("connection broken. Closing...")
                    self.connection_alive = False

                if data.startswith(b"{") and data.endswith(b"}\n"):
                    # split data by \n if we have multiple commands in socket buffer
                    data = data.split(b"\n")
                    # remove empty data
                    data.remove(b"")

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
                        threading.Event().wait(0.5)

                    # finally delete our rx buffer to be ready for new commands
                    data = bytes()
            except Exception as err:
                self.log.info(
                    "[SCK] Connection closed",
                    ip=self.client_address[0],
                    port=self.client_address[1],
                    e=err,
                )
                self.connection_alive = False

    def handle(self):
        """
        socket handler
        """
        CONNECTED_CLIENTS.add(self.request)

        self.log.debug(
            "[SCK] Client connected",
            ip=self.client_address[0],
            port=self.client_address[1],
        )
        self.connection_alive = True

        self.sendThread = threading.Thread(
            target=self.send_to_client, args=[], daemon=True
        )
        self.sendThread.start()
        self.receiveThread = threading.Thread(
            target=self.receive_from_client, args=[], daemon=True
        )
        self.receiveThread.start()

        # keep connection alive until we close it
        while self.connection_alive and not CLOSE_SIGNAL:
            threading.Event().wait(1)

    def finish(self):
        """ """
        self.log.warning(
            "[SCK] Closing client socket",
            ip=self.client_address[0],
            port=self.client_address[1],
        )
        try:
            CONNECTED_CLIENTS.remove(self.request)
        except Exception:
            self.log.warning(
                "[SCK] client connection already removed from client list",
                client=self.request,
            )


def process_tnc_commands(data):
    """
    process tnc commands

    Args:
      data:

    Returns:

    """
    log = structlog.get_logger("process_tnc_commands")

    # we need to do some error handling in case of socket timeout or decoding issue
    try:
        # convert data to json object
        received_json = json.loads(data)
        log.debug("[SCK] CMD", command=received_json)

        # ENABLE TNC LISTENING STATE -----------------------------------------------------
        if received_json["type"] == "set" and received_json["command"] == "listen":
            try:
                static.LISTEN = received_json["state"] in ['true', 'True', True, "ON", "on"]
                command_response("listen", True)

                # if tnc is connected, force disconnect when static.LISTEN == False
                if not static.LISTEN and static.ARQ_SESSION_STATE not in ["disconnecting", "disconnected", "failed"]:
                    DATA_QUEUE_TRANSMIT.put(["DISCONNECT"])
                    # set early disconnecting state so we can interrupt connection attempts
                    static.ARQ_SESSION_STATE = "disconnecting"
                    command_response("disconnect", True)

            except Exception as err:
                command_response("listen", False)
                log.warning(
                    "[SCK] CQ command execution error", e=err, command=received_json
                )

        # START STOP AUDIO RECORDING -----------------------------------------------------
        if received_json["type"] == "set" and received_json["command"] == "record_audio":
            try:
                if not static.AUDIO_RECORD:
                    static.AUDIO_RECORD_FILE = wave.open(f"{int(time.time())}_audio_recording.wav", 'w')
                    static.AUDIO_RECORD_FILE.setnchannels(1)
                    static.AUDIO_RECORD_FILE.setsampwidth(2)
                    static.AUDIO_RECORD_FILE.setframerate(8000)
                    static.AUDIO_RECORD = True
                else:
                    static.AUDIO_RECORD = False
                    static.AUDIO_RECORD_FILE.close()

                command_response("respond_to_call", True)

            except Exception as err:
                command_response("respond_to_call", False)
                log.warning(
                    "[SCK] CQ command execution error", e=err, command=received_json
                )


        # SET ENABLE/DISABLE RESPOND TO CALL -----------------------------------------------------
        if received_json["type"] == "set" and received_json["command"] == "respond_to_call":
            try:
                static.RESPOND_TO_CALL = received_json["state"] in ['true', 'True', True]
                command_response("respond_to_call", True)

            except Exception as err:
                command_response("respond_to_call", False)
                log.warning(
                    "[SCK] CQ command execution error", e=err, command=received_json
                )

        # SET ENABLE RESPOND TO CQ -----------------------------------------------------
        if received_json["type"] == "set" and received_json["command"] == "respond_to_cq":
            try:
                static.RESPOND_TO_CQ = received_json["state"] in ['true', 'True', True]
                command_response("respond_to_cq", True)

            except Exception as err:
                command_response("respond_to_cq", False)
                log.warning(
                    "[SCK] CQ command execution error", e=err, command=received_json
                )

        # SET TX AUDIO LEVEL  -----------------------------------------------------
        if (
            received_json["type"] == "set"
            and received_json["command"] == "tx_audio_level"
        ):
            try:
                static.TX_AUDIO_LEVEL = int(received_json["value"])
                command_response("tx_audio_level", True)

            except Exception as err:
                command_response("tx_audio_level", False)
                log.warning(
                    "[SCK] TX audio command execution error",
                    e=err,
                    command=received_json,
                )

        # TRANSMIT TEST FRAME  ----------------------------------------------------
        if (
            received_json["type"] == "set"
            and received_json["command"] == "send_test_frame"
        ):
            try:
                DATA_QUEUE_TRANSMIT.put(["SEND_TEST_FRAME"])
                command_response("send_test_frame", True)
            except Exception as err:
                command_response("send_test_frame", False)
                log.warning(
                    "[SCK] Send test frame command execution error",
                    e=err,
                    command=received_json,
                )

        # CQ CQ CQ -----------------------------------------------------
        if received_json["command"] == "cqcqcq":
            try:
                DATA_QUEUE_TRANSMIT.put(["CQ"])
                command_response("cqcqcq", True)

            except Exception as err:
                command_response("cqcqcq", False)
                log.warning(
                    "[SCK] CQ command execution error", e=err, command=received_json
                )

        # START_BEACON -----------------------------------------------------
        if received_json["command"] == "start_beacon":
            try:
                static.BEACON_STATE = True
                interval = int(received_json["parameter"])
                DATA_QUEUE_TRANSMIT.put(["BEACON", interval, True])
                command_response("start_beacon", True)
            except Exception as err:
                command_response("start_beacon", False)
                log.warning(
                    "[SCK] Start beacon command execution error",
                    e=err,
                    command=received_json,
                )

        # STOP_BEACON -----------------------------------------------------
        if received_json["command"] == "stop_beacon":
            try:
                log.warning("[SCK] Stopping beacon!")
                static.BEACON_STATE = False
                DATA_QUEUE_TRANSMIT.put(["BEACON", None, False])
                command_response("stop_beacon", True)
            except Exception as err:
                command_response("stop_beacon", False)
                log.warning(
                    "[SCK] Stop beacon command execution error",
                    e=err,
                    command=received_json,
                )

        # PING ----------------------------------------------------------
        if received_json["type"] == "ping" and received_json["command"] == "ping":
            # send ping frame and wait for ACK
            try:
                dxcallsign = received_json["dxcallsign"]
                if not str(dxcallsign).strip():
                    raise NoCallsign

                # additional step for being sure our callsign is correctly
                # in case we are not getting a station ssid
                # then we are forcing a station ssid = 0
                dxcallsign = helpers.callsign_to_bytes(dxcallsign)
                dxcallsign = helpers.bytes_to_callsign(dxcallsign)

                # check if specific callsign is set with different SSID than the TNC is initialized
                try:
                    mycallsign = received_json["mycallsign"]
                    mycallsign = helpers.callsign_to_bytes(mycallsign)
                    mycallsign = helpers.bytes_to_callsign(mycallsign)

                except Exception:
                    mycallsign = static.MYCALLSIGN

                DATA_QUEUE_TRANSMIT.put(["PING", mycallsign, dxcallsign])
                command_response("ping", True)
            except NoCallsign:
                command_response("ping", False)
                log.warning("[SCK] callsign required for ping", command=received_json)
            except Exception as err:
                command_response("ping", False)
                log.warning(
                    "[SCK] PING command execution error", e=err, command=received_json
                )

        # CONNECT ----------------------------------------------------------
        if received_json["type"] == "arq" and received_json["command"] == "connect":

            # pause our beacon first
            static.BEACON_PAUSE = True

            # check for connection attempts key
            try:
                attempts = int(received_json["attempts"])
            except Exception:
                # 15 == self.session_connect_max_retries
                attempts = 15

            dxcallsign = received_json["dxcallsign"]

            # check if specific callsign is set with different SSID than the TNC is initialized
            try:
                mycallsign = received_json["mycallsign"]
                mycallsign = helpers.callsign_to_bytes(mycallsign)
                mycallsign = helpers.bytes_to_callsign(mycallsign)

            except Exception:
                mycallsign = static.MYCALLSIGN

            # additional step for being sure our callsign is correctly
            # in case we are not getting a station ssid
            # then we are forcing a station ssid = 0
            dxcallsign = helpers.callsign_to_bytes(dxcallsign)
            dxcallsign = helpers.bytes_to_callsign(dxcallsign)

            if static.ARQ_SESSION_STATE not in ["disconnected", "failed"]:
                command_response("connect", False)
                log.warning(
                    "[SCK] Connect command execution error",
                    e=f"already connected to station:{static.DXCALLSIGN}",
                    command=received_json,
                )
            else:

                # finally check again if we are disconnected or failed

                # try connecting
                try:

                    DATA_QUEUE_TRANSMIT.put(["CONNECT", mycallsign, dxcallsign, attempts])
                    command_response("connect", True)
                except Exception as err:
                    command_response("connect", False)
                    log.warning(
                        "[SCK] Connect command execution error",
                        e=err,
                        command=received_json,
                    )
                    # allow beacon transmission again
                    static.BEACON_PAUSE = False

                # allow beacon transmission again
                static.BEACON_PAUSE = False

        # DISCONNECT ----------------------------------------------------------
        if received_json["type"] == "arq" and received_json["command"] == "disconnect":
            try:
                if static.ARQ_SESSION_STATE not in ["disconnecting", "disconnected", "failed"]:
                    DATA_QUEUE_TRANSMIT.put(["DISCONNECT"])

                    # set early disconnecting state so we can interrupt connection attempts
                    static.ARQ_SESSION_STATE = "disconnecting"
                    command_response("disconnect", True)
                else:
                    command_response("disconnect", False)
                    log.warning(
                        "[SCK] Disconnect command not possible",
                        state=static.ARQ_SESSION_STATE,
                        command=received_json,
                    )
            except Exception as err:
                command_response("disconnect", False)
                log.warning(
                    "[SCK] Disconnect command execution error",
                    e=err,
                    command=received_json,
                )

        # TRANSMIT RAW DATA -------------------------------------------
        if received_json["type"] == "arq" and received_json["command"] == "send_raw":
            static.BEACON_PAUSE = True

            # we need to reject a command processing if already in arq state
            if static.ARQ_STATE:
                command_response("send_raw", False)
                log.warning(
                    "[SCK] Send raw command execution error",
                    e="already in arq state",
                    command=received_json,
                )
                return False

            try:
                if not static.ARQ_SESSION:
                    dxcallsign = received_json["parameter"][0]["dxcallsign"]
                    # additional step for being sure our callsign is correctly
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
                    mycallsign = helpers.callsign_to_bytes(mycallsign)
                    mycallsign = helpers.bytes_to_callsign(mycallsign)

                except Exception:
                    mycallsign = static.MYCALLSIGN

                # check for connection attempts key
                try:
                    attempts = int(received_json["parameter"][0]["attempts"])

                except Exception:
                    # 15 == self.session_connect_max_retries
                    attempts = 10

                # check if transmission uuid provided else set no-uuid
                try:
                    arq_uuid = received_json["uuid"]
                except Exception:
                    arq_uuid = "no-uuid"

                if len(base64data) % 4:
                    raise TypeError

                binarydata = base64.b64decode(base64data)

                # wait some random time which acts as collision detection
                helpers.wait(randrange(0, 20, 5) / 10.0)

                DATA_QUEUE_TRANSMIT.put(
                    ["ARQ_RAW", binarydata, mode, n_frames, arq_uuid, mycallsign, dxcallsign, attempts]
                )

            except Exception as err:
                command_response("send_raw", False)
                log.warning(
                    "[SCK] Send raw command execution error",
                    e=err,
                    command=received_json,
                )

        # STOP TRANSMISSION ----------------------------------------------------------
        if (
            received_json["type"] == "arq"
            and received_json["command"] == "stop_transmission"
        ):
            try:
                if static.TNC_STATE == "BUSY" or static.ARQ_STATE:
                    DATA_QUEUE_TRANSMIT.put(["STOP"])
                log.warning("[SCK] Stopping transmission!")
                static.TNC_STATE = "IDLE"
                static.ARQ_STATE = False
                command_response("stop_transmission", True)
            except Exception as err:
                command_response("stop_transmission", False)
                log.warning(
                    "[SCK] STOP command execution error", e=err, command=received_json
                )

        if received_json["type"] == "get" and received_json["command"] == "rx_buffer":
            try:
                output = {
                    "command": "rx_buffer",
                    "data-array": [],
                }

                if not RX_BUFFER.empty():
                    for _buffer_length in range(RX_BUFFER.qsize()):
                        base64_data = RX_BUFFER.queue[_buffer_length][4]
                        output["data-array"].append(
                            {
                                "uuid": RX_BUFFER.queue[_buffer_length][0],
                                "timestamp": RX_BUFFER.queue[_buffer_length][1],
                                "dxcallsign": str(RX_BUFFER.queue[_buffer_length][2], "utf-8"),
                                "dxgrid": str(RX_BUFFER.queue[_buffer_length][3], "utf-8"),
                                "data": base64_data,
                            }
                        )
                    jsondata = json.dumps(output)
                    # self.request.sendall(bytes(jsondata, encoding))
                    SOCKET_QUEUE.put(jsondata)
                    command_response("rx_buffer", True)

            except Exception as err:
                command_response("rx_buffer", False)
                log.warning(
                    "[SCK] Send RX buffer command execution error",
                    e=err,
                    command=received_json,
                )

        if (
            received_json["type"] == "set"
            and received_json["command"] == "del_rx_buffer"
        ):
            try:
                RX_BUFFER.queue.clear()
                command_response("del_rx_buffer", True)
            except Exception as err:
                command_response("del_rx_buffer", False)
                log.warning(
                    "[SCK] Delete RX buffer command execution error",
                    e=err,
                    command=received_json,
                )

        # SET FREQUENCY -----------------------------------------------------
        if received_json["command"] == "frequency" and received_json["type"] == "set":
            try:
                RIGCTLD_COMMAND_QUEUE.put(["set_frequency", received_json["frequency"]])
                command_response("set_frequency", True)
            except Exception as err:
                command_response("set_frequency", False)
                log.warning(
                    "[SCK] Set frequency command execution error",
                    e=err,
                    command=received_json,
                )

        # SET MODE -----------------------------------------------------
        if received_json["command"] == "mode" and received_json["type"] == "set":
            try:
                RIGCTLD_COMMAND_QUEUE.put(["set_mode", received_json["mode"]])
                command_response("set_mode", True)
            except Exception as err:
                command_response("set_mode", False)
                log.warning(
                    "[SCK] Set mode command execution error",
                    e=err,
                    command=received_json,
                )

    # exception, if JSON cant be decoded
    except Exception as err:
        log.error("[SCK] JSON decoding error", e=err)


def send_tnc_state():
    """
    send the tnc state to network
    """
    encoding = "utf-8"

    output = {
        "command": "tnc_state",
        "ptt_state": str(static.PTT_STATE),
        "tnc_state": str(static.TNC_STATE),
        "arq_state": str(static.ARQ_STATE),
        "arq_session": str(static.ARQ_SESSION),
        "arq_session_state": str(static.ARQ_SESSION_STATE),
        "audio_dbfs": str(static.AUDIO_DBFS),
        "snr": str(static.SNR),
        "frequency": str(static.HAMLIB_FREQUENCY),
        "speed_level": str(static.ARQ_SPEED_LEVEL),
        "mode": str(static.HAMLIB_MODE),
        "bandwidth": str(static.HAMLIB_BANDWIDTH),
        "fft": str(static.FFT),
        "channel_busy": str(static.CHANNEL_BUSY),
        "scatter": static.SCATTER,
        "rx_buffer_length": str(RX_BUFFER.qsize()),
        "rx_msg_buffer_length": str(len(static.RX_MSG_BUFFER)),
        "arq_bytes_per_minute": str(static.ARQ_BYTES_PER_MINUTE),
        "arq_bytes_per_minute_burst": str(static.ARQ_BYTES_PER_MINUTE_BURST),
        "arq_seconds_until_finish": str(static.ARQ_SECONDS_UNTIL_FINISH),
        "arq_compression_factor": str(static.ARQ_COMPRESSION_FACTOR),
        "arq_transmission_percent": str(static.ARQ_TRANSMISSION_PERCENT),
        "speed_list": static.SPEED_LIST,
        "total_bytes": str(static.TOTAL_BYTES),
        "beacon_state": str(static.BEACON_STATE),
        "stations": [],
        "mycallsign": str(static.MYCALLSIGN, encoding),
        "mygrid": str(static.MYGRID, encoding),
        "dxcallsign": str(static.DXCALLSIGN, encoding),
        "dxgrid": str(static.DXGRID, encoding),
        "hamlib_status": static.HAMLIB_STATUS,
        "listen": str(static.LISTEN),
        "audio_recording": str(static.AUDIO_RECORD),
    }

    # add heard stations to heard stations object
    for heard in static.HEARD_STATIONS:
        output["stations"].append(
            {
                "dxcallsign": str(heard[0], "utf-8"),
                "dxgrid": str(heard[1], "utf-8"),
                "timestamp": heard[2],
                "datatype": heard[3],
                "snr": heard[4],
                "offset": heard[5],
                "frequency": heard[6],
            }
        )
    return json.dumps(output)


# This appears to have been taken out of a class, but is never called because
# the `self.request.sendall` call is a syntax error as `self` is undefined and
# we don't see errors in use.
def process_daemon_commands(data):
    """
    process daemon commands

    Args:
      data:

    Returns:

    """
    log = structlog.get_logger("process_daemon_commands")

    # convert data to json object
    received_json = json.loads(data)
    log.debug("[SCK] CMD", command=received_json)
    if received_json["type"] == "set" and received_json["command"] == "mycallsign":
        try:
            callsign = received_json["parameter"]

            if bytes(callsign, "utf-8") == b"":
                self.request.sendall(b"INVALID CALLSIGN")
                log.warning(
                    "[SCK] SET MYCALL FAILED",
                    call=static.MYCALLSIGN,
                    crc=static.MYCALLSIGN_CRC.hex(),
                )
            else:
                static.MYCALLSIGN = bytes(callsign, "utf-8")
                static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)

                command_response("mycallsign", True)
                log.info(
                    "[SCK] SET MYCALL",
                    call=static.MYCALLSIGN,
                    crc=static.MYCALLSIGN_CRC.hex(),
                )
        except Exception as err:
            command_response("mycallsign", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    if received_json["type"] == "set" and received_json["command"] == "mygrid":
        try:
            mygrid = received_json["parameter"]

            if bytes(mygrid, "utf-8") == b"":
                self.request.sendall(b"INVALID GRID")
                command_response("mygrid", False)
            else:
                static.MYGRID = bytes(mygrid, "utf-8")
                log.info("[SCK] SET MYGRID", grid=static.MYGRID)
                command_response("mygrid", True)
        except Exception as err:
            command_response("mygrid", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    if (
        received_json["type"] == "set"
        and received_json["command"] == "start_tnc"
        and not static.TNCSTARTED
    ):
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
            low_bandwidth_mode = str(
                received_json["parameter"][0]["low_bandwidth_mode"]
            )
            tuning_range_fmin = str(received_json["parameter"][0]["tuning_range_fmin"])
            tuning_range_fmax = str(received_json["parameter"][0]["tuning_range_fmax"])
            tx_audio_level = str(received_json["parameter"][0]["tx_audio_level"])
            respond_to_cq = str(received_json["parameter"][0]["respond_to_cq"])
            rx_buffer_size = str(received_json["parameter"][0]["rx_buffer_size"])
            enable_explorer = str(received_json["parameter"][0]["enable_explorer"])

            try:
                # convert ssid list to python list
                ssid_list = str(received_json["parameter"][0]["ssid_list"])
                ssid_list = ssid_list.replace(" ", "")
                ssid_list = ssid_list.split(",")
                # convert str to int
                ssid_list = list(map(int, ssid_list))
            except KeyError:
                ssid_list = [0]

            # print some debugging parameters
            for item in received_json["parameter"][0]:
                log.debug(
                    f"[SCK] TNC Startup Config : {item}",
                    value=received_json["parameter"][0][item],
                )

            DAEMON_QUEUE.put(
                [
                    "STARTTNC",
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
                    low_bandwidth_mode,
                    tuning_range_fmin,
                    tuning_range_fmax,
                    enable_fsk,
                    tx_audio_level,
                    respond_to_cq,
                    rx_buffer_size,
                    enable_explorer,
                    ssid_list,
                ]
            )
            command_response("start_tnc", True)

        except Exception as err:
            command_response("start_tnc", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    if received_json["type"] == "get" and received_json["command"] == "test_hamlib":
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

            DAEMON_QUEUE.put(
                [
                    "TEST_HAMLIB",
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
                ]
            )
            command_response("test_hamlib", True)
        except Exception as err:
            command_response("test_hamlib", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    if received_json["type"] == "set" and received_json["command"] == "stop_tnc":
        try:
            static.TNCPROCESS.kill()
            # unregister process from atexit to avoid process zombies
            atexit.unregister(static.TNCPROCESS.kill)

            log.warning("[SCK] Stopping TNC")
            static.TNCSTARTED = False
            command_response("stop_tnc", True)
        except Exception as err:
            command_response("stop_tnc", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)


def send_daemon_state():
    """
    send the daemon state to network
    """
    log = structlog.get_logger("send_daemon_state")

    try:
        python_version = f"{str(sys.version_info[0])}.{str(sys.version_info[1])}"

        output = {
            "command": "daemon_state",
            "daemon_state": [],
            "python_version": str(python_version),
            "hamlib_version": static.HAMLIB_VERSION,
            "input_devices": static.AUDIO_INPUT_DEVICES,
            "output_devices": static.AUDIO_OUTPUT_DEVICES,
            "serial_devices": static.SERIAL_DEVICES,
            #'cpu': str(psutil.cpu_percent()),
            #'ram': str(psutil.virtual_memory().percent),
            "version": "0.1",
        }

        if static.TNCSTARTED:
            output["daemon_state"].append({"status": "running"})
        else:
            output["daemon_state"].append({"status": "stopped"})

        return json.dumps(output)
    except Exception as err:
        log.warning("[SCK] error", e=err)
        return None


def command_response(command, status):
    s_status = "OK" if status else "Failed"
    jsondata = {"command_response": command, "status": s_status}
    data_out = json.dumps(jsondata)
    SOCKET_QUEUE.put(data_out)

