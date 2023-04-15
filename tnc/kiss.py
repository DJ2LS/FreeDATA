import threading
import socketserver
import static
from enum import Enum
from queues import DATA_QUEUE_TRANSMIT
import helpers
import structlog
import queue

log = structlog.get_logger("kiss")

TRANSMIT_QUEUE = queue.Queue()
CONNECTED_CLIENTS = set()
CALLSIGNS = set() # total registerd callsigns
CLOSE_SIGNAL = False


class KISS_FRAMES(Enum):
    """
    Enumeration for kiss frame types
    """
    FEND = b'\xC0'
    FESC = b'\xDB'
    TFEND = b'\xDC'
    TFESC = b'\xDD'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class KISS:
    def encode_callsign(self):
        pass

    def decode_callsign(self):
        pass


class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    connection_alive = False
    log = structlog.get_logger("ThreadedTCPRequestHandler")

    def send_to_client(self):
        # data dispatcher
        # sending data via socket only to registered callsign
        while True:
            # rest override state
            override = False

            if TRANSMIT_QUEUE.qsize() > 0:
                command = TRANSMIT_QUEUE.get()
                print(command)
                # send data to client
                # do this via separate functions for each frame type

            threading.Event().wait(0.1)

    def receive_from_client(self):
        data = b''
        while self.connection_alive and not CLOSE_SIGNAL:
            try:
                chunk = self.request.recv(1024)
                data += chunk

                if chunk == b"":
                    # print("connection broken. Closing...")
                    self.connection_alive = False

                if data.startswith(KISS_FRAMES.FEND.value) and data.endswith(KISS_FRAMES.FEND.value) and data not in [b'']:
                    commands = data.split(KISS_FRAMES.FEND.value)

                    for i in range(0, commands.count(b'')):
                        commands.remove(b'')
                    for command in commands:
                        self.log.warning(
                            f"[KISS] [AX.25]",
                            raw = command,
                            ip=self.client_address[0],
                            port=self.client_address[1],
                        )
                        print(command)


                    data = b''
                else:
                    self.log.info(
                        "[KISS] Unknown frame received",
                        frame=data,
                        ip=self.client_address[0],
                        port=self.client_address[1],
                    )

            except Exception as err:
                self.log.error(
                    "[KISS] Connection closed",
                    ip=self.client_address[0],
                    port=self.client_address[1],
                    e=err,
                )
                self.connection_alive = False




    def handle(self):
        self.REGISTERED_CALLSIGN_FOR_SOCKET = set()
        CONNECTED_CLIENTS.add(self.request)



        self.log.debug(
            "[KISS] Client connected",
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
            "[KISS] Closing client socket",
            ip=self.client_address[0],
            port=self.client_address[1],
        )
        try:
            CONNECTED_CLIENTS.remove(self.request)
        except Exception as e:
            self.log.warning(
                "[KISS] client connection already removed from client list",
                client=self.request,
                e=e,
            )




    def send_to_socket(self, data_out:bytes):
        #self.send_to_socket(bytes(frame))
        try:
            self.request.send(data_out)
        except Exception as err:
            self.log.error(
                "[KISS] socket error",
                ip=self.client_address[0],
                port=self.client_address[1],
                error=err
            )

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

