import threading
import socketserver
import static
from enum import Enum
from queues import DATA_QUEUE_TRANSMIT
import helpers
import structlog
import queue

log = structlog.get_logger("agwpe")

TRANSMIT_QUEUE = queue.Queue()
CONNECTED_CLIENTS = set()
CALLSIGNS = set() # total registerd callsigns
CLOSE_SIGNAL = False


class AGWPE_FRAMES(Enum):
    """
    Enumeration for codec2 modes and names
    """
    register_call = b'X'  # register callsign
    unregister_call = b'x'  # unregister callsign
    enable_monitoring = b'm'  # Start monitoring
    enable_monitoring_raw = b'k'  # Start monitoring using raw frames
    connect_request = b'C'  # Start an AX.25 connection
    connect_request_nonstandard = b'c'  # Start a non-standard AX.25 connection (data frames would have PID not 0xF0)
    get_ports = b'G'
    disconnect = b'd'  # Disconnect an AX.25 connection
    heard_stations = b'H'  # Heard Stations
    get_version = b'R'  # AGWPE Version
    send_unproto_info = b'M'  # Send Unproto Info  --> Broadcasted
    send_unproto_info_via = b'V'  # Send Unproto Info VIA  --> Broadcasted

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class AGWPE:
    def decode(self, frame):
        port = frame[0:1]
        reserved1 = frame[1:4]
        DataKind = frame[4:5]
        reserved2 = frame[5:6]
        PID = frame[6:7]
        reserved3 = frame[7:8]
        CallFrom = frame[8:18]
        CallTo = frame[18:28]
        DataLen = frame[28:32]
        User = frame[32:36]
        Payload = frame[36:]

        #print(CallFrom)
        # ignore empty callsigns
        if CallFrom not in [bytes(10)]:
            # ignore callsigns already having a SSID
            if b'-' not in CallFrom:
                #if CallFrom.strip(b'\x00')[:-2] not in [b'-']:
                call = CallFrom.strip(b'\x00')
                call += b'-0'
                CallFrom = bytearray(10)
                CallFrom[:len(call)] = call
                CallFrom = bytes(CallFrom)

        # ignore empty callsigns
        if CallTo not in [bytes(10)]:
            # ignore callsigns already having a SSID
            if b'-' not in CallTo:
                #if CallFrom.strip(b'\x00')[:-2] not in [b'-']:
                call = CallTo.strip(b'\x00')
                call += b'-0'
                CallTo = bytearray(10)
                CallTo[:len(call)] = call
                CallTo = bytes(CallTo)

        return {"port": port,
                "reserved1": reserved1,
                "DataKind": DataKind,
                "reserved2": reserved2,
                "PID": PID,
                "reserved3": reserved3,
                "CallTo": CallTo,
                "CallFrom": CallFrom,
                "DataLen": DataLen,
                "User": User,
                "Payload": Payload
                }

    def encode_agwpe_frame(self, DataKind: str, CallTo:bytes = bytes(10), CallFrom:bytes = bytes(10), Payload: bytes=b'', PID:bytes=bytes(1) ):
        frame = bytearray(36)
        frame[4:5] = bytes(DataKind, 'ascii')
        frame[5:6] = PID
        frame[8:18] = CallTo
        frame[18:28] = CallFrom
        frame[28:32] = int(len(Payload)).to_bytes(4, byteorder="little", signed=False)
        frame += Payload
        return bytes(frame)

class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    connection_alive = False
    log = structlog.get_logger("ThreadedTCPRequestHandler")

    def send_to_client(self):
        # data dispatcher
        # sending data via socket only to registered callsign
        while True:

            if TRANSMIT_QUEUE.qsize() > 0:
                #print(TRANSMIT_QUEUE.queue[0])
                #print(self.REGISTERED_CALLSIGN_FOR_SOCKET)

                # check if FIFO command callsign is equal to registered one, else ignore it
                # QUEUE.queue[n] is a way of accessing elements in queue without removing them, like with ".get()"
                if TRANSMIT_QUEUE.queue[0][0] in self.REGISTERED_CALLSIGN_FOR_SOCKET:
                    command = TRANSMIT_QUEUE.get()
                    print(command)

                    # [0] = CallFrom
                    # [1] = CallTo
                    # [2] = State like "connecting/connected/..../data"
                    # [3] = Payload

                    if command[2] == "connected":
                        self.send_to_client_connected(CallFrom=command[0], CallTo=command[1])
                    else:
                        self.log.error(
                            "[AGWPE] No commmand in stack",
                            command=command,
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )

                else:
                    # no callsign match - lets ignore it
                    pass

            threading.Event().wait(0.1)

    def receive_from_client(self):
        data = b''
        while True:

            chunk = self.request.recv(1024)
            data += chunk
            defaultAGWPElength = 36

            if len(data) % defaultAGWPElength == 0 and AGWPE_FRAMES.has_value(data[4:5]):
                frames = [data[i:i + defaultAGWPElength] for i in range(0, len(data), defaultAGWPElength)]
                for frame in frames:
                    decoded_frame = AGWPE().decode(frame)
                    #print(decoded_frame)

                    if decoded_frame["DataKind"] == AGWPE_FRAMES.register_call.value:
                        
                        if decoded_frame["CallFrom"] not in CALLSIGNS:
                            
                            self.REGISTERED_CALLSIGN_FOR_SOCKET = decoded_frame["CallFrom"]

                            data_out = AGWPE().encode_agwpe_frame(CallFrom=decoded_frame["CallFrom"],
                                                                  DataKind="X",
                                                                  Payload=bytes([1])
                                                                  )
                            self.request.sendall(data_out)
                            self.log.info(
                                "[AGWPE] Registered callsign",
                                call=decoded_frame["CallFrom"],
                                ip=self.client_address[0],
                                port=self.client_address[1],
                            )
                        
                        else:

                            data_out = AGWPE().encode_agwpe_frame(CallFrom=decoded_frame["CallFrom"],
                                                                  DataKind="X",
                                                                  Payload=bytes([0])
                                                                  )
                            self.request.sendall(data_out)
                            self.log.warning(
                                "[AGWPE] Callsign already registered",
                                call=decoded_frame["CallFrom"],
                                ip=self.client_address[0],
                                port=self.client_address[1],
                            )
                        
                    elif decoded_frame["DataKind"] == AGWPE_FRAMES.enable_monitoring.value:
                        self.log.info(
                            "[AGWPE] Enable monitoring",
                            info="not yet implemented",
                            call=decoded_frame["CallFrom"],
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )

                    elif decoded_frame["DataKind"] == AGWPE_FRAMES.get_ports.value:
                        self.log.info(
                            "[AGWPE] request ports",
                            info="only one device yet",
                            call=decoded_frame["CallFrom"],
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )

                        ports = bytes(f'1;Port1 FreeDATA HF TNC {static.HAMLIB_FREQUENCY};', 'ascii')
                        data_out = AGWPE().encode_agwpe_frame(CallTo=decoded_frame["CallTo"],
                                                              CallFrom=decoded_frame["CallFrom"], DataKind="G",
                                                              Payload=ports)
                        self.request.sendall(data_out)

                    elif decoded_frame["DataKind"] == AGWPE_FRAMES.heard_stations.value:
                        info = bytes(f'LU7DID-4 Mon,21Feb2000 11:14:30 Mon,21Feb2000 12:18:22', 'ascii')
                        data_out = AGWPE().encode_agwpe_frame(CallTo=decoded_frame["CallFrom"],
                                                              CallFrom=decoded_frame["CallTo"],
                                                              PID=decoded_frame["PID"],
                                                              DataKind="H",
                                                              Payload=info
                                                              )
                        self.request.sendall(data_out)

                    elif decoded_frame["DataKind"] == AGWPE_FRAMES.connect_request.value:
                        self.log.info(
                            "[AGWPE] connecting",
                            CallTo=decoded_frame["CallTo"],
                            CallFrom=decoded_frame["CallFrom"],
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )

                        self.tnc_arq_connect(decoded_frame)
                        while static.ARQ_SESSION_STATE in ["connecting", "disconnected"]:
                            threading.Event().wait(0.1)

                        if static.ARQ_SESSION_STATE == "connected":
                            """
                            self.log.info(
                                "[AGWPE] connected",
                                CallTo=decoded_frame["CallTo"],
                                CallFrom=decoded_frame["CallFrom"],
                                ip=self.client_address[0],
                                port=self.client_address[1],
                            )

                            info = bytes(f'*** CONNECTED With {decoded_frame["CallTo"]}', 'ascii')
                            data_out = AGWPE().encode_agwpe_frame(CallTo=decoded_frame["CallFrom"],
                                                                  CallFrom=decoded_frame["CallTo"],
                                                                  PID=decoded_frame["PID"],
                                                                  DataKind="C",
                                                                  Payload=info)
                            self.request.sendall(data_out)
                            """
                            pass
                        else:
                            self.log.warning(
                                "[AGWPE] connection failed",
                                CallTo=decoded_frame["CallTo"],
                                CallFrom=decoded_frame["CallFrom"],
                                ip=self.client_address[0],
                                port=self.client_address[1],
                            )

                    elif decoded_frame["DataKind"] == AGWPE_FRAMES.disconnect.value:
                        self.log.warning(
                            "[AGWPE] disconnecting",
                            CallTo=decoded_frame["CallTo"],
                            CallFrom=decoded_frame["CallFrom"],
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )

                        self.tnc_arq_disconnect(decoded_frame)
                        while static.ARQ_SESSION_STATE in ["disconnecting", "connected", "connecting"]:
                            threading.Event().wait(0.1)

                        data_out = AGWPE().encode_agwpe_frame(CallTo=decoded_frame["CallFrom"],
                                                              CallFrom=decoded_frame["CallTo"], DataKind="d")
                        self.request.sendall(data_out)
                        self.log.info(
                            "[AGWPE] disconnected",
                            CallTo=decoded_frame["CallTo"],
                            CallFrom=decoded_frame["CallFrom"],
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )

                    elif decoded_frame["DataKind"] == AGWPE_FRAMES.get_version.value:
                        self.log.info(
                            "[AGWPE] request version",
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )

                        version = bytes(static.VERSION, 'ascii')
                        data_out = AGWPE().encode_agwpe_frame(DataKind="G", Payload=version)
                        self.request.sendall(data_out)

                    else:
                        print("------------")
                        print(data)
                        # disconnect

                    data = b''

            # area for frames with non default length of 36 bytes
            else:

                if AGWPE_FRAMES.has_value(data[4:5]):
                    print("has value check")
                    decoded_frame = AGWPE().decode(data)

                    print(
                        len(b'\x00\x00\x00\x00V\x00\xf0\x00DJ2LS\x00\x00\x00\x00\x00APX216\x00\x00\x00\x00]\x00\x00\x00\x00\x00\x00\x00\x01WIDE2-2\x00\x00\x00:DN2LS    :1111111111111111111111111111111111111111111111111111111111111111111{06}'))

                    if decoded_frame["DataKind"] == AGWPE_FRAMES.send_unproto_info.value:
                        print("send unproto info")
                        # Callsign info switched here
                        print(f"CallTo: {decoded_frame['CallFrom']}")
                        print(f"CallFrom: {decoded_frame['CallTo']}")
                        print(decoded_frame['CallFrom'])

                        payload = bytes("PR", "ascii")
                        payload += decoded_frame['CallFrom']  # to
                        payload += decoded_frame['CallTo']  # from
                        payload += decoded_frame["Payload"]

                        DATA_QUEUE_TRANSMIT.put(["FEC", payload, 'datac3'])

                    elif decoded_frame["DataKind"] == AGWPE_FRAMES.send_unproto_info_via.value:
                        print("send unproto info via")  #
                        # Callsign info switched here
                        print(f"CallTo: {decoded_frame['CallFrom']}")
                        print(f"CallFrom: {decoded_frame['CallTo']}")

                        payload = bytes("PR", "ascii")
                        payload += decoded_frame['CallFrom']  # to
                        payload += decoded_frame['CallTo']  # from
                        payload += decoded_frame["Payload"]

                        DATA_QUEUE_TRANSMIT.put(["FEC", decoded_frame["Payload"], 'datac3'])

                elif data not in [b'']:
                    print("empty check")
                    print(data)

                data = b''

    def handle(self):
        self.REGISTERED_CALLSIGN_FOR_SOCKET = b''
        CONNECTED_CLIENTS.add(self.request)



        self.log.debug(
            "[AGWPE] Client connected",
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


    def send_heard_stations(self):
        """
        LU7DID-4 Mon,21Feb2000 11:14:30 Mon,21Feb2000 12:18:22

        "H" Frame

        """
        pass

    def tnc_arq_connect(self, decoded_frame):

        # pause our beacon first
        static.BEACON_PAUSE = True

        attempts = 15

        dxcallsign = decoded_frame["CallTo"][:-3]
        print(dxcallsign)
        # check if specific callsign is set with different SSID than the TNC is initialized
        try:
            mycallsign = decoded_frame["CallFrom"][:-3]
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
        
            log.warning(
                "[AGWPE] Connect command execution error",
                e=f"already connected to station:{static.DXCALLSIGN}",
                command=decoded_frame,
            )
        else:

            # finally check again if we are disconnected or failed

            # try connecting
            try:

                DATA_QUEUE_TRANSMIT.put(["CONNECT", mycallsign, dxcallsign, attempts])
            except Exception as err:
                log.warning(
                    "[AGWPE] Connect command execution error",
                    e=err,
                    command=decoded_frame,
                )
                # allow beacon transmission again
                static.BEACON_PAUSE = False

            # allow beacon transmission again
            static.BEACON_PAUSE = False

    def tnc_arq_disconnect(self, decoded_frame):
        try:
            if static.ARQ_SESSION_STATE not in ["disconnecting", "disconnected", "failed"]:
                DATA_QUEUE_TRANSMIT.put(["DISCONNECT"])

                # set early disconnecting state so we can interrupt connection attempts
                static.ARQ_SESSION_STATE = "disconnecting"
                #command_response("disconnect", True)
            else:
                #command_response("disconnect", False)
                log.warning(
                    "[AGWPE] Disconnect command not possible",
                    state=static.ARQ_SESSION_STATE,
                    command=decoded_frame,
                )
        except Exception as err:
            #command_response("disconnect", False)
            log.warning(
                "[AGWPE] Disconnect command execution error",
                e=err,
                command=decoded_frame,
            )

    def send_to_client_connected(self, CallFrom: bytes = bytes(10), CallTo: bytes = bytes(10) ):

        self.log.info(
            "[AGWPE] connected",
            CallTo=CallTo,
            CallFrom=CallFrom,
            ip=self.client_address[0],
            port=self.client_address[1],
        )

        info = bytes(f'*** CONNECTED With {CallTo}', 'ascii')
        data_out = AGWPE().encode_agwpe_frame(CallTo=CallTo,
                                              CallFrom=CallFrom,
                                              PID=b'',
                                              DataKind="C",
                                              Payload=info)
        self.request.sendall(data_out)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

