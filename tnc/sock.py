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
from static import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, TNC
import structlog
from random import randrange
import ujson as json
from exceptions import NoCallsign
from queues import DATA_QUEUE_TRANSMIT, RX_BUFFER, RIGCTLD_COMMAND_QUEUE

SOCKET_QUEUE = queue.Queue()
DAEMON_QUEUE = queue.Queue()

CONNECTED_CLIENTS = set()
CLOSE_SIGNAL = False

TESTMODE = False

log = structlog.get_logger("sock")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    the socket handler base class
    """

    pass


# noinspection PyTypeChecker
class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    """ """
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
            if self.server.server_address[1] == TNC.port and not Daemon.tncstarted:
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
                            # TODO: Check if we really should set connection alive to false.
                            # This might disconnect all other clients as well...
                            self.connection_alive = False
                except Exception as err:
                    self.log.debug("[SCK] catch harmless RuntimeError: Set changed size during iteration", e=err)

            # we want to transmit scatter data only once to reduce network traffic
            ModemParam.scatter = []
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
                        if self.server.server_address[1] == TNC.port:
                            self.process_tnc_commands(commands)
                        else:
                            self.process_daemon_commands(commands)

                        # wait some time between processing multiple commands
                        # this is only a first test to avoid doubled transmission
                        # we might improve this by only processing one command or
                        # doing some kind of selection to determine which commands need to be dropped
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
        except Exception as e:
            self.log.warning(
                "[SCK] client connection already removed from client list",
                client=self.request,
                e=e,
            )

    # ------------------------ TNC COMMANDS
    def process_tnc_commands(self, data):
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

            # ENABLE TNC LISTENING STATE
            if received_json["type"] == "set" and received_json["command"] == "listen":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_listen(None, received_json)
                else:
                    self.tnc_set_listen(received_json)

            # START STOP AUDIO RECORDING
            if received_json["type"] == "set" and received_json["command"] == "record_audio":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_record_audio(None, received_json)
                else:
                    self.tnc_set_record_audio(received_json)

            # SET ENABLE/DISABLE RESPOND TO CALL
            if received_json["type"] == "set" and received_json["command"] == "respond_to_call":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_respond_to_call(None, received_json)
                else:
                    self.tnc_set_respond_to_call(received_json)

            # SET ENABLE RESPOND TO CQ
            if received_json["type"] == "set" and received_json["command"] == "respond_to_cq":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_record_audio(None, received_json)
                else:
                    self.tnc_set_record_audio(received_json)
            # SET TX AUDIO LEVEL
            if received_json["type"] == "set" and received_json["command"] == "tx_audio_level":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_tx_audio_level(None, received_json)
                else:
                    self.tnc_set_tx_audio_level(received_json)
            # TRANSMIT TEST FRAME
            if received_json["type"] == "set" and received_json["command"] == "send_test_frame":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_send_test_frame(None, received_json)
                elif TNC.tnc_state in ['busy']:
                    log.warning(
                        "[SCK] Dropping command",
                        e="tnc state",
                        state=TNC.tnc_state,
                        command=received_json,
                    )
                else:
                    self.tnc_set_send_test_frame(received_json)

            # TRANSMIT FEC FRAME
            if received_json["type"] == "fec" and received_json["command"] == "transmit":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_fec_transmit(None, received_json)
                else:
                    self.tnc_fec_transmit(received_json)

            # TRANSMIT IS WRITING FRAME
            if received_json["type"] == "fec" and received_json["command"] == "transmit_is_writing":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_fec_is_writing(None, received_json)
                elif TNC.tnc_state in ['busy']:
                    log.warning(
                        "[SCK] Dropping command",
                        e="tnc state",
                        state=TNC.tnc_state,
                        command=received_json,
                    )
                else:
                    self.tnc_fec_is_writing(received_json)

            # CQ CQ CQ
            if received_json["command"] == "cqcqcq":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_cqcqcq(None, received_json)
                elif TNC.tnc_state in ['busy']:
                    log.warning(
                        "[SCK] Dropping command",
                        e="tnc state",
                        state=TNC.tnc_state,
                        command=received_json,
                    )
                else:
                    self.tnc_cqcqcq(received_json)

            # START_BEACON
            if received_json["command"] == "start_beacon":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_start_beacon(None, received_json)
                else:
                    self.tnc_start_beacon(received_json)

            # STOP_BEACON
            if received_json["command"] == "stop_beacon":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_stop_beacon(None, received_json)
                else:
                    self.tnc_stop_beacon(received_json)

            # PING
            if received_json["type"] == "ping" and received_json["command"] == "ping":

                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_ping_ping(None, received_json)
                elif TNC.tnc_state in ['busy']:
                    log.warning(
                        "[SCK] Dropping command",
                        e="tnc state",
                        state=TNC.tnc_state,
                        command=received_json,
                    )

                else:
                    self.tnc_ping_ping(received_json)

            # CONNECT
            if received_json["type"] == "arq" and received_json["command"] == "connect":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_arq_connect(None, received_json)
                elif TNC.tnc_state in ['busy']:
                    log.warning(
                        "[SCK] Dropping command",
                        e="tnc state",
                        state=TNC.tnc_state,
                        command=received_json,
                    )
                else:
                    self.tnc_arq_connect(received_json)

            # DISCONNECT
            if received_json["type"] == "arq" and received_json["command"] == "disconnect":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_arq_disconnect(None, received_json)
                else:
                    self.tnc_arq_disconnect(received_json)

            # TRANSMIT RAW DATA
            if received_json["type"] == "arq" and received_json["command"] == "send_raw":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_arq_send_raw(None, received_json)
                elif TNC.tnc_state in ['busy']:
                    log.warning(
                        "[SCK] Dropping command",
                        e="tnc state",
                        state=TNC.tnc_state,
                        command=received_json,
                    )
                else:
                    self.tnc_arq_send_raw(received_json)

            # STOP TRANSMISSION
            if received_json["type"] == "arq" and received_json["command"] == "stop_transmission":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_arq_stop_transmission(None, received_json)
                else:
                    self.tnc_arq_stop_transmission(received_json)

            # GET RX BUFFER
            if received_json["type"] == "get" and received_json["command"] == "rx_buffer":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_get_rx_buffer(None, received_json)
                else:
                    self.tnc_get_rx_buffer(received_json)

            # DELETE RX BUFFER
            if received_json["type"] == "set" and received_json["command"] == "del_rx_buffer":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_del_rx_buffer(None, received_json)
                else:
                    self.tnc_set_del_rx_buffer(received_json)
            # SET FREQUENCY
            if received_json["type"] == "set" and received_json["command"] == "frequency":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_frequency(None, received_json)
                else:
                    self.tnc_set_frequency(received_json)

            # SET MODE
            if received_json["type"] == "set" and received_json["command"] == "mode":
                if TESTMODE:
                    ThreadedTCPRequestHandler.tnc_set_mode(None, received_json)
                else:
                    self.tnc_set_mode(received_json)

        except Exception as err:
            log.error("[SCK] JSON decoding error", e=err)

    def tnc_set_listen(self, received_json):
        try:
            TNC.listen = received_json["state"] in ['true', 'True', True, "ON", "on"]
            command_response("listen", True)

            # if tnc is connected, force disconnect when TNC.listen == False
            if not TNC.listen and ARQ.arq_session_state not in ["disconnecting", "disconnected", "failed"]:
                DATA_QUEUE_TRANSMIT.put(["DISCONNECT"])
                # set early disconnecting state so we can interrupt connection attempts
                ARQ.arq_session_state = "disconnecting"
                command_response("disconnect", True)

        except Exception as err:
            command_response("listen", False)
            log.warning(
                "[SCK] CQ command execution error", e=err, command=received_json
            )

    def tnc_set_record_audio(self, received_json):
        try:
            if not AudioParam.audio_record:
                AudioParam.audio_record_FILE = wave.open(f"{int(time.time())}_audio_recording.wav", 'w')
                AudioParam.audio_record_FILE.setnchannels(1)
                AudioParam.audio_record_FILE.setsampwidth(2)
                AudioParam.audio_record_FILE.setframerate(8000)
                AudioParam.audio_record = True
            else:
                AudioParam.audio_record = False
                AudioParam.audio_record_FILE.close()

            command_response("respond_to_call", True)

        except Exception as err:
            command_response("respond_to_call", False)
            log.warning(
                "[SCK] CQ command execution error", e=err, command=received_json
            )

    def tnc_set_respond_to_call(self, received_json):
        try:
            TNC.respond_to_call = received_json["state"] in ['true', 'True', True]
            command_response("respond_to_call", True)

        except Exception as err:
            command_response("respond_to_call", False)
            log.warning(
                "[SCK] CQ command execution error", e=err, command=received_json
            )

    def tnc_set_respond_to_cq(self, received_json):
        try:
            TNC.respond_to_cq = received_json["state"] in ['true', 'True', True]
            command_response("respond_to_cq", True)

        except Exception as err:
            command_response("respond_to_cq", False)
            log.warning(
                "[SCK] CQ command execution error", e=err, command=received_json
            )

    def tnc_set_tx_audio_level(self, received_json):
        try:
            AudioParam.tx_audio_level = int(received_json["value"])
            command_response("tx_audio_level", True)

        except Exception as err:
            command_response("tx_audio_level", False)
            log.warning(
                "[SCK] TX audio command execution error",
                e=err,
                command=received_json,
            )

    def tnc_set_send_test_frame(self, received_json):
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

    def tnc_fec_transmit(self, received_json):
        try:
            mode = received_json["mode"]
            base64data = received_json["payload"]
            if len(base64data) % 4:
                raise TypeError
            payload = base64.b64decode(base64data)

            DATA_QUEUE_TRANSMIT.put(["FEC", payload, mode])
            command_response("fec_transmit", True)
        except Exception as err:
            command_response("fec_transmit", False)
            log.warning(
                "[SCK] Send fec frame command execution error",
                e=err,
                command=received_json,
            )

    def tnc_fec_is_writing(self, received_json):
        try:
            mycallsign = received_json["mycallsign"]
            DATA_QUEUE_TRANSMIT.put(["FEC_IS_WRITING", mycallsign])
            command_response("fec_is_writing", True)
        except Exception as err:
            command_response("fec_is_writing", False)
            log.warning(
                "[SCK] Send fec frame command execution error",
                e=err,
                command=received_json,
            )

    def tnc_cqcqcq(self, received_json):
        try:
            DATA_QUEUE_TRANSMIT.put(["CQ"])
            command_response("cqcqcq", True)

        except Exception as err:
            command_response("cqcqcq", False)
            log.warning(
                "[SCK] CQ command execution error", e=err, command=received_json
            )

    def tnc_start_beacon(self, received_json):
        try:
            Beacon.beacon_state = True
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

    def tnc_stop_beacon(self, received_json):
        try:
            log.warning("[SCK] Stopping beacon!")
            Beacon.beacon_state = False
            DATA_QUEUE_TRANSMIT.put(["BEACON", None, False])
            command_response("stop_beacon", True)
        except Exception as err:
            command_response("stop_beacon", False)
            log.warning(
                "[SCK] Stop beacon command execution error",
                e=err,
                command=received_json,
            )

    def tnc_ping_ping(self, received_json):
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
                mycallsign = Station.mycallsign

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

    def tnc_arq_connect(self, received_json):

        # pause our beacon first
        Beacon.beacon_pause = True

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
            mycallsign = Station.mycallsign

        # additional step for being sure our callsign is correctly
        # in case we are not getting a station ssid
        # then we are forcing a station ssid = 0
        dxcallsign = helpers.callsign_to_bytes(dxcallsign)
        dxcallsign = helpers.bytes_to_callsign(dxcallsign)

        if ARQ.arq_session_state not in ["disconnected", "failed"]:
            command_response("connect", False)
            log.warning(
                "[SCK] Connect command execution error",
                e=f"already connected to station:{Station.dxcallsign}",
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
                Beacon.beacon_pause = False

            # allow beacon transmission again
            Beacon.beacon_pause = False

    def tnc_arq_disconnect(self, received_json):
        try:
            if ARQ.arq_session_state not in ["disconnecting", "disconnected", "failed"]:
                DATA_QUEUE_TRANSMIT.put(["DISCONNECT"])

                # set early disconnecting state so we can interrupt connection attempts
                ARQ.arq_session_state = "disconnecting"
                command_response("disconnect", True)
            else:
                command_response("disconnect", False)
                log.warning(
                    "[SCK] Disconnect command not possible",
                    state=ARQ.arq_session_state,
                    command=received_json,
                )
        except Exception as err:
            command_response("disconnect", False)
            log.warning(
                "[SCK] Disconnect command execution error",
                e=err,
                command=received_json,
            )

    def tnc_arq_send_raw(self, received_json):
        Beacon.beacon_pause = True

        # wait some random time
        helpers.wait(randrange(5, 25, 5) / 10.0)

        # we need to warn if already in arq state
        if ARQ.arq_state:
            command_response("send_raw", False)
            log.warning(
                "[SCK] Send raw command execution warning",
                e="already in arq state",
                i="command queued",
                command=received_json,
            )

        try:
            if not ARQ.arq_session:
                dxcallsign = received_json["parameter"][0]["dxcallsign"]
                # additional step for being sure our callsign is correctly
                # in case we are not getting a station ssid
                # then we are forcing a station ssid = 0
                dxcallsign = helpers.callsign_to_bytes(dxcallsign)
                dxcallsign = helpers.bytes_to_callsign(dxcallsign)
                Station.dxcallsign = dxcallsign
                Station.dxcallsign_crc = helpers.get_crc_24(Station.dxcallsign)
                command_response("send_raw", True)
            else:
                dxcallsign = Station.dxcallsign
                Station.dxcallsign_crc = helpers.get_crc_24(Station.dxcallsign)

            mode = int(received_json["parameter"][0]["mode"])
            n_frames = int(received_json["parameter"][0]["n_frames"])
            base64data = received_json["parameter"][0]["data"]

            # check if specific callsign is set with different SSID than the TNC is initialized
            try:
                mycallsign = received_json["parameter"][0]["mycallsign"]
                mycallsign = helpers.callsign_to_bytes(mycallsign)
                mycallsign = helpers.bytes_to_callsign(mycallsign)

            except Exception:
                mycallsign = Station.mycallsign

            # check for connection attempts key
            try:
                attempts = int(received_json["parameter"][0]["attempts"])

            except Exception:
                attempts = 10

            # check if transmission uuid provided else set no-uuid
            try:
                arq_uuid = received_json["uuid"]
            except Exception:
                arq_uuid = "no-uuid"

            if len(base64data) % 4:
                raise TypeError

            binarydata = base64.b64decode(base64data)

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

    def tnc_arq_stop_transmission(self, received_json):
        try:
            if TNC.tnc_state == "BUSY" or ARQ.arq_state:
                DATA_QUEUE_TRANSMIT.put(["STOP"])
            log.warning("[SCK] Stopping transmission!")
            TNC.tnc_state = "IDLE"
            ARQ.arq_state = False
            command_response("stop_transmission", True)
        except Exception as err:
            command_response("stop_transmission", False)
            log.warning(
                "[SCK] STOP command execution error", e=err, command=received_json
            )

    def tnc_get_rx_buffer(self, received_json):
        try:
            if not RX_BUFFER.empty():
                output = {
                    "command": "rx_buffer",
                    "data-array": [],
                }

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

    def tnc_set_del_rx_buffer(self, received_json):
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

    def tnc_set_mode(self, received_json):
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

    def tnc_set_frequency(self, received_json):
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

    # ------------------------ DAEMON COMMANDS
    def process_daemon_commands(self, data):
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
            self.daemon_set_mycallsign(received_json)

        if received_json["type"] == "set" and received_json["command"] == "mygrid":
            self.daemon_set_mygrid(received_json)

        if (
                received_json["type"] == "set"
                and received_json["command"] == "start_tnc"
                and not Daemon.tncstarted
        ):
            self.daemon_start_tnc(received_json)

        if received_json["type"] == "get" and received_json["command"] == "test_hamlib":
            self.daemon_test_hamlib(received_json)

        if received_json["type"] == "set" and received_json["command"] == "stop_tnc":
            self.daemon_stop_tnc(received_json)

    def daemon_set_mycallsign(self, received_json):
        try:
            callsign = received_json["parameter"]

            if bytes(callsign, "utf-8") == b"":
                self.request.sendall(b"INVALID CALLSIGN")
                log.warning(
                    "[SCK] SET MYCALL FAILED",
                    call=Station.mycallsign,
                    crc=Station.mycallsign_crc.hex(),
                )
            else:
                Station.mycallsign = bytes(callsign, "utf-8")
                Station.mycallsign_crc = helpers.get_crc_24(Station.mycallsign)

                command_response("mycallsign", True)
                log.info(
                    "[SCK] SET MYCALL",
                    call=Station.mycallsign,
                    crc=Station.mycallsign_crc.hex(),
                )
        except Exception as err:
            command_response("mycallsign", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    def daemon_set_mygrid(self, received_json):
        try:
            mygrid = received_json["parameter"]

            if bytes(mygrid, "utf-8") == b"":
                self.request.sendall(b"INVALID GRID")
                command_response("mygrid", False)
            else:
                Station.mygrid = bytes(mygrid, "utf-8")
                log.info("[SCK] SET MYGRID", grid=Station.mygrid)
                command_response("mygrid", True)
        except Exception as err:
            command_response("mygrid", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    def daemon_start_tnc(self, received_json):
        try:
            startparam = received_json["parameter"][0]

            mycall = str(helpers.return_key_from_object("AA0AA", startparam, "mycall"))
            mygrid = str(helpers.return_key_from_object("JN12ab", startparam, "mygrid"))
            rx_audio = str(helpers.return_key_from_object("0", startparam, "rx_audio"))
            tx_audio = str(helpers.return_key_from_object("0", startparam, "tx_audio"))
            radiocontrol = str(helpers.return_key_from_object("disabled", startparam, "radiocontrol"))
            rigctld_ip = str(helpers.return_key_from_object("127.0.0.1", startparam, "rigctld_ip"))
            rigctld_port = str(helpers.return_key_from_object("4532", startparam, "rigctld_port"))
            enable_scatter = str(helpers.return_key_from_object("True", startparam, "enable_scatter"))
            enable_fft = str(helpers.return_key_from_object("True", startparam, "enable_fft"))
            enable_fsk = str(helpers.return_key_from_object("False", startparam, "enable_fsk"))
            low_bandwidth_mode = str(helpers.return_key_from_object("False", startparam, "low_bandwidth_mode"))
            tuning_range_fmin = str(helpers.return_key_from_object("-50", startparam, "tuning_range_fmin"))
            tuning_range_fmax = str(helpers.return_key_from_object("50", startparam, "tuning_range_fmax"))
            tx_audio_level = str(helpers.return_key_from_object("100", startparam, "tx_audio_level"))
            respond_to_cq = str(helpers.return_key_from_object("False", startparam, "respond_to_cq"))
            rx_buffer_size = str(helpers.return_key_from_object("16", startparam, "rx_buffer_size"))
            enable_explorer = str(helpers.return_key_from_object("False", startparam, "enable_explorer"))
            enable_auto_tune = str(helpers.return_key_from_object("False", startparam, "enable_auto_tune"))
            enable_stats = str(helpers.return_key_from_object("False", startparam, "enable_stats"))
            tx_delay = str(helpers.return_key_from_object("0", startparam, "tx_delay"))
            try:
                # convert ssid list to python list
                ssid_list = str(helpers.return_key_from_object("0, 1, 2, 3, 4, 5, 6, 7, 8, 9", startparam, "ssid_list"))
                ssid_list = ssid_list.replace(" ", "")
                ssid_list = ssid_list.split(",")
                # convert str to int
                ssid_list = list(map(int, ssid_list))
            except KeyError:
                ssid_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

            # print some debugging parameters
            for item in startparam:
                log.debug(
                    f"[SCK] TNC Startup Config : {item}",
                    value=startparam[item],
                )

            DAEMON_QUEUE.put(
                [
                    "STARTTNC",
                    mycall,
                    mygrid,
                    rx_audio,
                    tx_audio,
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
                    enable_auto_tune,
                    enable_stats,
                    tx_delay
                ]
            )
            command_response("start_tnc", True)

        except Exception as err:
            command_response("start_tnc", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    def daemon_stop_tnc(self, received_json):
        try:
            Daemon.tncprocess.kill()
            # unregister process from atexit to avoid process zombies
            atexit.unregister(Daemon.tncprocess.kill)

            log.warning("[SCK] Stopping TNC")
            Daemon.tncstarted = False
            command_response("stop_tnc", True)
        except Exception as err:
            command_response("stop_tnc", False)
            log.warning("[SCK] command execution error", e=err, command=received_json)

    def daemon_test_hamlib(self, received_json):
        try:
            radiocontrol = str(received_json["parameter"][0]["radiocontrol"])
            rigctld_ip = str(received_json["parameter"][0]["rigctld_ip"])
            rigctld_port = str(received_json["parameter"][0]["rigctld_port"])

            DAEMON_QUEUE.put(
                [
                    "TEST_HAMLIB",
                    radiocontrol,
                    rigctld_ip,
                    rigctld_port,
                ]
            )
            command_response("test_hamlib", True)
        except Exception as err:
            command_response("test_hamlib", False)
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
            "input_devices": AudioParam.audio_input_devices,
            "output_devices": AudioParam.audio_output_devices,
            "serial_devices": Daemon.serial_devices,
            # 'cpu': str(psutil.cpu_percent()),
            # 'ram': str(psutil.virtual_memory().percent),
            "version": "0.1",
        }

        if Daemon.tncstarted:
            output["daemon_state"].append({"status": "running"})
        else:
            output["daemon_state"].append({"status": "stopped"})

        return json.dumps(output)
    except Exception as err:
        log.warning("[SCK] error", e=err)
        return None


def send_tnc_state():
    """
    send the tnc state to network
    """
    encoding = "utf-8"
    output = {
        "command": "tnc_state",
        "ptt_state": str(HamlibParam.ptt_state),
        "tnc_state": str(TNC.tnc_state),
        "arq_state": str(ARQ.arq_state),
        "arq_session": str(ARQ.arq_session),
        "arq_session_state": str(ARQ.arq_session_state),
        "audio_dbfs": str(AudioParam.audio_dbfs),
        "snr": str(ModemParam.snr),
        "frequency": str(HamlibParam.hamlib_frequency),
        "rf_level": str(HamlibParam.hamlib_rf),
        "strength": str(HamlibParam.hamlib_strength),
        "alc": str(HamlibParam.alc),
        "audio_level": str(AudioParam.tx_audio_level),
        "audio_auto_tune": str(AudioParam.audio_auto_tune),
        "speed_level": str(ARQ.arq_speed_level),
        "mode": str(HamlibParam.hamlib_mode),
        "bandwidth": str(HamlibParam.hamlib_bandwidth),
        "fft": str(AudioParam.fft),
        "channel_busy": str(ModemParam.channel_busy),
        "channel_busy_slot": str(ModemParam.channel_busy_slot),
        "is_codec2_traffic": str(ModemParam.is_codec2_traffic),
        "scatter": ModemParam.scatter,
        "rx_buffer_length": str(RX_BUFFER.qsize()),
        "rx_msg_buffer_length": str(len(ARQ.rx_msg_buffer)),
        "arq_bytes_per_minute": str(ARQ.bytes_per_minute),
        "arq_bytes_per_minute_burst": str(ARQ.bytes_per_minute_burst),
        "arq_seconds_until_finish": str(ARQ.arq_seconds_until_finish),
        "arq_compression_factor": str(ARQ.arq_compression_factor),
        "arq_transmission_percent": str(ARQ.arq_transmission_percent),
        "speed_list": ARQ.speed_list,
        "total_bytes": str(ARQ.total_bytes),
        "beacon_state": str(Beacon.beacon_state),
        "stations": [],
        "mycallsign": str(Station.mycallsign, encoding),
        "mygrid": str(Station.mygrid, encoding),
        "dxcallsign": str(Station.dxcallsign, encoding),
        "dxgrid": str(Station.dxgrid, encoding),
        "hamlib_status": HamlibParam.hamlib_status,
        "listen": str(TNC.listen),
        "audio_recording": str(AudioParam.audio_record),
    }

    # add heard stations to heard stations object
    for heard in TNC.heard_stations:
        output["stations"].append(
            {
                "dxcallsign": str(heard[0], encoding),
                "dxgrid": str(heard[1], encoding),
                "timestamp": heard[2],
                "datatype": heard[3],
                "snr": heard[4],
                "offset": heard[5],
                "frequency": heard[6],
            }
        )
    return json.dumps(output)


def command_response(command, status):
    s_status = "OK" if status else "Failed"
    jsondata = {"command_response": command, "status": s_status}
    data_out = json.dumps(jsondata)
    SOCKET_QUEUE.put(data_out)


def try_except(string):
    try:
        return string
    except Exception:
        return False
