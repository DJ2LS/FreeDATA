import threading
from enum import Enum
from modem_frametypes import FRAME_TYPE
from codec2 import FREEDV_MODE
import data_frame_factory
import structlog
import random
from queue import Queue
import time
from arq_data_type_handler import ARQDataTypeHandler, ARQ_SESSION_TYPES
from arq_session_iss import ARQSessionISS
import helpers
import zlib

class States(Enum):
    NEW = 0
    CONNECTING = 1
    CONNECT_SENT = 2
    CONNECT_ACK_SENT = 3
    CONNECTED = 4
    AWAITING_DATA = 5
    #HEARTBEAT_SENT = 5
    #HEARTBEAT_ACK_SENT = 6
    PAYLOAD_SENT = 7
    ARQ_SESSION = 8
    DISCONNECTING = 9
    DISCONNECTED = 10
    ABORTED = 11
    FAILED = 12


class P2PConnection:
    STATE_TRANSITION = {
        States.NEW: {
            FRAME_TYPE.P2P_CONNECTION_CONNECT.value: 'connected_irs',
        },
        States.CONNECTING: {
            FRAME_TYPE.P2P_CONNECTION_CONNECT_ACK.value: 'connected_iss',
        },
        States.CONNECTED: {
            FRAME_TYPE.P2P_CONNECTION_CONNECT.value: 'connected_irs',
            FRAME_TYPE.P2P_CONNECTION_CONNECT_ACK.value: 'connected_iss',
            FRAME_TYPE.P2P_CONNECTION_PAYLOAD.value: 'received_data',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
            FRAME_TYPE.P2P_CONNECTION_HEARTBEAT.value: 'received_heartbeat',
            FRAME_TYPE.P2P_CONNECTION_HEARTBEAT_ACK.value: 'received_heartbeat_ack',

        },
        States.PAYLOAD_SENT: {
            FRAME_TYPE.P2P_CONNECTION_PAYLOAD_ACK.value: 'transmitted_data',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
            FRAME_TYPE.P2P_CONNECTION_HEARTBEAT.value: 'received_heartbeat',
            FRAME_TYPE.P2P_CONNECTION_HEARTBEAT_ACK.value: 'received_heartbeat_ack',

        },
        States.AWAITING_DATA: {
            FRAME_TYPE.P2P_CONNECTION_PAYLOAD.value: 'transmitted_data',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
            FRAME_TYPE.P2P_CONNECTION_HEARTBEAT_ACK.value: 'received_heartbeat_ack',
        },
        States.ARQ_SESSION: {
            FRAME_TYPE.P2P_CONNECTION_PAYLOAD_ACK.value: 'transmitted_data',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
            FRAME_TYPE.P2P_CONNECTION_HEARTBEAT_ACK.value: 'received_heartbeat_ack',

        },
        States.DISCONNECTING: {
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT_ACK.value: 'received_disconnect_ack',
        },
        States.DISCONNECTED: {
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT_ACK.value: 'received_disconnect_ack',

        },
        States.ABORTED:{
        },
        States.FAILED: {
        },
    }

    def __init__(self, ctx, origin: str, destination: str):
        self.ctx = ctx
        self.logger = structlog.get_logger(type(self).__name__)

        self.frame_factory = data_frame_factory.DataFrameFactory(self.ctx)


        self.destination = destination
        self.destination_crc = helpers.get_crc_24(destination)
        self.origin = origin
        self.bandwidth = 2300

        if self.ctx.rf_modem:
            self.ctx.rf_modem.demodulator.set_decode_mode(is_p2p_connection=True)

        self.p2p_data_tx_queue = Queue()
        #Remove after testing
        self.p2p_data_rx_queue = Queue()

        self.arq_data_type_handler = ARQDataTypeHandler(self.ctx)


        self.state = States.NEW
        self.session_id = self.generate_id()

        self.event_frame_received = threading.Event()



        self.RETRIES_CONNECT = 3
        self.TIMEOUT_CONNECT = 5
        self.TIMEOUT_DATA = 5
        self.RETRIES_DATA = 5
        self.ENTIRE_CONNECTION_TIMEOUT = 180

        self.is_ISS = False # Indicator, if we are ISS or IRS
        self.is_Master = False # Indicator, if we are Maste or Not


        self.last_data_timestamp= time.time()
        self.start_data_processing_worker()

        self.flag_has_data = False
        self.flag_announce_arq = False

        self.transmission_in_progress = False # indicatews, if we are waiting for an ongoing transmission

    def start_data_processing_worker(self):
        """Starts a worker thread to monitor the transmit data queue and process data."""

        def data_processing_worker():
            while True:
                if time.time() > self.last_data_timestamp + self.ENTIRE_CONNECTION_TIMEOUT and self.state not in [States.DISCONNECTING, States.DISCONNECTED, States.ARQ_SESSION, States.FAILED]:
                    self.disconnect()
                    return

                # thats our heartbeat logic, only ISS will run it
                if time.time() > self.last_data_timestamp + 15 and self.state is States.CONNECTED and self.is_ISS and not self.transmission_in_progress:
                    print("no data within last 15s. Sending heartbeat")

                    if self.p2p_data_tx_queue.empty():
                        self.flag_has_data = False
                    else:
                        self.flag_has_data = True
                    self.transmit_heartbeat(has_data=self.flag_has_data)

                if self.state == States.CONNECTED and self.is_Master:
                    self.process_data_queue()

                threading.Event().wait(0.500)

                if self.state is not States.ARQ_SESSION and self.is_Master:
                    threading.Event().wait(5)
                    self.process_data_queue()



        # Create and start the worker thread
        worker_thread = threading.Thread(target=data_processing_worker, daemon=True)
        worker_thread.start()

    def generate_id(self):
        while True:
            random_int = random.randint(1,255)
            if random_int not in self.ctx.state_manager.p2p_connection_sessions:
                return random_int

            if len(self.ctx.state_manager.p2p_connection_sessions) >= 255:
                return False

    def set_details(self, snr, frequency_offset):
        self.snr = snr
        self.frequency_offset = frequency_offset

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}][id={self.session_id}][state={self.state}][ISS={bool(self.is_ISS)}][Master={bool(self.is_Master)}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def set_state(self, state):
        if self.state == state:
            self.log(f"{type(self).__name__} state {self.state.name} unchanged.")
        else:
            self.log(f"{type(self).__name__} state change from {self.state.name} to {state.name}")
        self.state = state

    def on_frame_received(self, frame):
        self.last_data_timestamp = time.time()
        self.event_frame_received.set()
        self.log(f"Received {frame['frame_type']}")
        frame_type = frame['frame_type_int']
        if self.state in self.STATE_TRANSITION:
            if frame_type in self.STATE_TRANSITION[self.state]:
                action_name = self.STATE_TRANSITION[self.state][frame_type]
                response = getattr(self, action_name)(frame)

                return

        self.log(f"Ignoring unknown transition from state {self.state.name} with frame {frame['frame_type']}")

    def transmit_frame(self, frame: bytearray, mode='auto'):
        self.log("Transmitting frame")
        if mode in ['auto']:
            mode = self.get_mode_by_speed_level(self.speed_level)

        self.ctx.rf_modem.transmit(mode, 1, 1, frame)

    def transmit_wait_and_retry(self, frame_or_burst, timeout, retries, mode):
        while retries > 0:
            self.event_frame_received = threading.Event()
            self.transmission_in_progress = True
            if isinstance(frame_or_burst, list): burst = frame_or_burst
            else: burst = [frame_or_burst]
            for f in burst:
                self.transmit_frame(f, mode)
            self.event_frame_received.clear()
            self.log(f"Waiting {timeout} seconds...")
            if self.event_frame_received.wait(timeout):
                self.transmission_in_progress = False
                return
            self.log("Timeout!")
            retries = retries - 1

        #self.connected_iss() # override connection state for simulation purposes
        self.session_failed()

    def launch_twr(self, frame_or_burst, timeout, retries, mode):
        twr = threading.Thread(target = self.transmit_wait_and_retry, args=[frame_or_burst, timeout, retries, mode], daemon=True)
        twr.start()

    def transmit_and_wait_irs(self, frame, timeout, mode):
        self.event_frame_received.clear()
        self.transmit_frame(frame, mode)
        self.log(f"Waiting {timeout} seconds...")
        #if not self.event_frame_received.wait(timeout):
        #    self.log("Timeout waiting for ISS. Session failed.")
        #    self.transmission_failed()

    def launch_twr_irs(self, frame, timeout, mode):
        thread_wait = threading.Thread(target = self.transmit_and_wait_irs,
                                       args = [frame, timeout, mode], daemon=True)
        thread_wait.start()

    def connect(self):
        self.set_state(States.CONNECTING)
        self.is_ISS = True
        self.last_data_timestamp = time.time()
        session_open_frame = self.frame_factory.build_p2p_connection_connect(self.destination, self.origin, self.session_id)
        self.launch_twr(session_open_frame, self.TIMEOUT_CONNECT, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        return

    def connected_iss(self, frame=None):
        self.log("CONNECTED ISS...........................")
        self.set_state(States.CONNECTED)
        self.is_ISS = True
        self.is_Master = True
        if self.ctx.socket_interface_manager and hasattr(self.ctx.socket_interface_manager.command_server, "command_handler"):
            self.ctx.socket_interface_manager.command_server.command_handler.socket_respond_connected(self.origin, self.destination, self.bandwidth)

    def connected_irs(self, frame):
        self.log("CONNECTED IRS...........................")
        self.ctx.state_manager.register_p2p_connection_session(self)
        self.ctx.socket_interface_manager.command_server.command_handler.session = self
        self.set_state(States.CONNECTED)
        self.is_ISS = False
        self.is_Master = False
        self.origin = frame["origin"]
        self.destination = frame["destination"]
        self.destination_crc = frame["destination_crc"]
        #self.log(frame)

        self.log(f"destination: {self.destination} - origin: {self.origin}")


        if self.ctx.socket_interface_manager and hasattr(self.ctx.socket_interface_manager.command_server, "command_handler"):
            self.ctx.socket_interface_manager.command_server.command_handler.socket_respond_connected(self.origin, self.destination, self.bandwidth)

        session_open_frame = self.frame_factory.build_p2p_connection_connect_ack(self.destination, self.origin, self.session_id)
        self.launch_twr_irs(session_open_frame, self.ENTIRE_CONNECTION_TIMEOUT, mode=FREEDV_MODE.signalling)

    def session_failed(self):
        self.set_state(States.FAILED)
        if self.ctx.socket_interface_manager and hasattr(self.ctx.socket_interface_manager.command_server, "command_handler"):
            self.ctx.socket_interface_manager.command_server.command_handler.socket_respond_disconnected()


    def process_data_queue(self, frame=None):
        if self.p2p_data_tx_queue.empty():
            self.is_Master = False
            return

        self.is_Master = True
        print("processing data....")

        raw_data = self.p2p_data_tx_queue.get()
        sequence_id = random.randint(0,255)

        compressor = zlib.compressobj(level=6, wbits=-zlib.MAX_WBITS, strategy=zlib.Z_FILTERED)
        data = compressor.compress(raw_data) + compressor.flush()

        if  len(data) <= 11:
            mode = FREEDV_MODE.signalling
        elif 11 < len(data) <= 32:
            mode = FREEDV_MODE.datac4
        else:
            self.transmit_arq(raw_data)
            return

        if self.p2p_data_tx_queue.empty():
            self.flag_has_data = False
        else:
            self.flag_has_data = True

        payload = self.frame_factory.build_p2p_connection_payload(mode, self.session_id, sequence_id, data, flag_has_data=self.flag_has_data)
        self.launch_twr(payload, self.TIMEOUT_DATA, self.RETRIES_DATA,mode=mode)
        self.set_state(States.PAYLOAD_SENT)

        return

    def received_data(self, frame):
        self.log(f"received data...: {frame}")

        ack_data = self.frame_factory.build_p2p_connection_payload_ack(self.session_id, 0)
        self.launch_twr_irs(ack_data, self.ENTIRE_CONNECTION_TIMEOUT, mode=FREEDV_MODE.signalling_ack)

        if not frame["flag"]["HAS_DATA"] and self.is_ISS:
            self.set_state(States.CONNECTED)
        else:
            self.set_state(States.AWAITING_DATA)

        try:
            received_data = frame['data'].rstrip(b'\x00')

            decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
            received_data = decompressor.decompress(received_data)
            received_data += decompressor.flush()

            if self.ctx.socket_interface_manager and hasattr(self.ctx.socket_interface_manager.data_server, "data_handler"):
                self.log(f"sending {len(received_data)} bytes to data socket client")
                self.ctx.socket_interface_manager.data_server.data_handler.send_data_to_client(received_data)

        except Exception as e:
            self.log(f"Error sending data to socket: {e}")




    def transmitted_data(self, frame):
        print("transmitted data...")
        self.set_state(States.CONNECTED)

    def transmit_heartbeat(self, has_data=False, announce_arq=False):
        # heartbeats will be transmit by ISS only, therefore only IRS can reveice heartbeat ack
        self.last_data_timestamp = time.time()

        heartbeat = self.frame_factory.build_p2p_connection_heartbeat(self.session_id, flag_has_data=has_data, flag_announce_arq=announce_arq)
        self.launch_twr(heartbeat, 6, 10, mode=FREEDV_MODE.signalling)

    def transmit_heartbeat_ack(self):
        print("transmit heartbeat ack")

        if self.p2p_data_tx_queue.empty():
            self.flag_has_data = False
        else:
            self.flag_has_data = True

        self.last_data_timestamp = time.time()
        heartbeat_ack = self.frame_factory.build_p2p_connection_heartbeat_ack(self.session_id, flag_has_data=self.flag_has_data,flag_announce_arq=self.flag_announce_arq)
        print(heartbeat_ack)
        self.launch_twr_irs(heartbeat_ack, self.ENTIRE_CONNECTION_TIMEOUT, mode=FREEDV_MODE.signalling)

    def received_heartbeat(self, frame):
        # we don't accept heartbeats as ISS
        if self.is_ISS:
            return
        print("received heartbeat...")
        self.last_data_timestamp = time.time()

        if frame["flag"]["HAS_DATA"]:
            print("other station has data")
            self.is_Master = False

        else:

            if self.p2p_data_tx_queue.empty():
                print("other station's buffer is empty as well. We won't become data master now")
                self.is_Master = False
                self.flag_has_data = False
            else:
                print("other station's buffer is empty. We can become data master now")
                self.is_Master = True
                self.flag_has_data = True



        if frame["flag"]["ANNOUNCE_ARQ"]:
            print("other station announced ARQ, changing state")
            self.is_Master = False
            self.set_state(States.ARQ_SESSION)
        print("transmit heartbeat ack")
        self.transmit_heartbeat_ack()

    def received_heartbeat_ack(self, frame):
        self.last_data_timestamp = time.time()
        print("received heartbeat ack from IRS...")

        if frame["flag"]["HAS_DATA"] and not self.flag_has_data:
            print("other station has data, we are not")
            self.is_Master = False
            self.set_state(States.AWAITING_DATA)
        elif frame["flag"]["HAS_DATA"] and self.flag_has_data:
            print("other station has data and we as well, we become master")
            self.is_Master = True
            self.set_state(States.CONNECTED)
        else:
            print("other station has no data, we become master now")
            self.is_Master = True
            self.set_state(States.CONNECTED)

        if frame["flag"]["ANNOUNCE_ARQ"]:
            print("other station announced arq, changing state")
            self.is_Master = False
            self.set_state(States.ARQ_SESSION)

        self.event_frame_received.set()



    def disconnect(self):
        if self.state not in [States.DISCONNECTING, States.DISCONNECTED, States.ARQ_SESSION]:
            self.set_state(States.DISCONNECTING)
            disconnect_frame = self.frame_factory.build_p2p_connection_disconnect(self.session_id)
            self.launch_twr(disconnect_frame, self.TIMEOUT_CONNECT, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        return

    def abort_connection(self):
        # abort is a dirty disconnect
        self.log("ABORTING...............")
        self.event_frame_received.set()
        self.set_state(States.DISCONNECTED)

    def received_disconnect(self, frame):
        self.log("DISCONNECTED...............")
        self.set_state(States.DISCONNECTED)
        if self.ctx.socket_interface_manager:
            self.ctx.socket_interface_manager.command_server.command_handler.socket_respond_disconnected()
        self.is_ISS = False
        disconnect_ack_frame = self.frame_factory.build_p2p_connection_disconnect_ack(self.session_id)
        self.launch_twr_irs(disconnect_ack_frame, self.ENTIRE_CONNECTION_TIMEOUT, mode=FREEDV_MODE.signalling)

    def received_disconnect_ack(self, frame):
        self.log("DISCONNECTED...............")
        self.set_state(States.DISCONNECTED)
        if self.ctx.socket_interface_manager:
            self.ctx.socket_interface_manager.command_server.command_handler.socket_respond_disconnected()



    def transmit_arq(self, data):
        """
        This function needs to be fixed - we want to send ARQ data within a p2p connection
        check p2p_connection handler in arq_data_type_handler

        """
        self.set_state(States.ARQ_SESSION)
        if self.is_ISS:
            arq_destination = self.destination
        else:
            arq_destination = self.origin

        #self.log(f"ANNOUNCING ARQ to destination: {self.destination}")
        #heartbeat = self.frame_factory.build_p2p_connection_heartbeat(self.session_id, flag_has_data=False, flag_announce_arq=True)
        #self.launch_twr(heartbeat, 5, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        #self.event_frame_received.wait()
        #self.log(f"ARQ destination: {self.destination}")
        #self.transmit_heartbeat(announce_arq=True)
        print("wait some time until ARQ starts....")
        threading.Event().wait(5)

        prepared_data, type_byte = self.arq_data_type_handler.prepare(data, ARQ_SESSION_TYPES.p2p_connection)
        iss = ARQSessionISS(self.ctx, arq_destination, prepared_data, type_byte)
        iss.id = self.session_id
        # register p2p connection to arq session
        iss.running_p2p_connection = self

        if iss.id:
            self.ctx.state_manager.register_arq_iss_session(iss)
            iss.start()
            return iss

    def transmitted_arq(self, transmitted_data):
        self.last_data_timestamp = time.time()
        self.set_state(States.CONNECTED)
        self.is_Master = True

    def received_arq(self, received_data):
        self.last_data_timestamp = time.time()
        self.set_state(States.CONNECTED)

        try:
            if self.ctx.socket_interface_manager and hasattr(self.ctx.socket_interface_manager.data_server, "data_handler"):
                self.log(f"sending {len(received_data)} bytes to data socket client")
                self.ctx.socket_interface_manager.data_server.data_handler.send_data_to_client(received_data)

        except Exception as e:
            self.log(f"Error sending data to socket: {e}")

    def failed_arq(self):
        self.set_state(States.CONNECTED)
