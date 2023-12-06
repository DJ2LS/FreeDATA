import threading
import data_frame_factory
import queue
import random
from codec2 import FREEDV_MODE
import arq_session

class ARQSessionISS(arq_session.ARQSession):

    STATE_DISCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2
    STATE_SENDING = 3

    STATE_ENDED = 10

    RETRIES_CONNECT = 3
    RETRIES_TRANSFER = 3

    TIMEOUT_CONNECT_ACK = 5
    TIMEOUT_TRANSFER = 2

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str, data: bytearray):
        super().__init__(config, tx_frame_queue, dxcall)
        self.data = data

        self.state = self.STATE_DISCONNECTED
        self.id = self.generate_id()

        self.event_connection_ack_received = threading.Event()
        self.event_transfer_ack_received = threading.Event()
        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

    def generate_id(self):
        return random.randint(1,255)

    def log(self, message):
        pass

    def set_state(self, state):
        self.log(f"ARQ Session {self.id} state {self.state}")
        self.state = state

    def runner(self):
        if not self.connect():
            return False
    
        return self.send_data()
    
    def run(self):
        self.thread = threading.Thread(target=self.runner, name=f"ARQ ISS Session {self.id}", daemon=True)
        self.thread.run()
    
    def connect(self):
        self.state =  self.STATE_CONNECTING

        connect_frame = self.frame_factory.build_arq_session_connect(True, self.dxcall, self.id)

        retries = self.RETRIES_CONNECT
        while retries > 0:
            self.transmit_frame(connect_frame)
            if self.event_connection_ack_received.wait(self.TIMEOUT_CONNECT_ACK):
                self.setState(self.STATE_CONNECTED)
                return True
            retries = retries - 1

        self.setState(self.STATE_DISCONNECTED)
        return False

    def on_connection_ack_received(self, ack):
        if self.state != self.STATE_CONNECTING:
            raise RuntimeError(f"ARQ Session: Received connection ACK while in state {self.state}")

        self.speed_level = ack['speed_level']
        self.event_connection_ack_received.set()

    # Sends the full payload in multiple frames
    def send_data(self):
        offset = 0
        while offset < len(self.data):
            max_size = self.get_max_size_for_speed_level(self.speed_level)
            end_offset = min(len(self.data), max_size)
            frame_payload = self.data[offset:end_offset]
            data_frame = self.frame_factory.build_arq_session_send(self.speed_level, 
                                                                   self.dxcall, 
                                                                   frame_payload)
            self.set_state(self.STATE_SENDING)
            if not self.send_arq(data_frame):
                return False
            offset = end_offset + 1

    # Send part of the payload using ARQ
    def send_arq(self, frame):
        retries = self.RETRIES_TRANSFER
        while retries > 0:
            # to know later if it has changed
            speed_level = self.speed_level
            self.transmit_frame(frame)
            # wait for ack
            if self.event_transfer_ack_received.wait(self.TIMEOUT_TRANSFER):
                speed_level = self.speed_level
                return True
            
            # don't decrement retries if speed level is changing
            if self.speed_level == speed_level:
                retries = retries - 1

        self.set_state(self.STATE_DISCONNECTED)
        return False

    def on_transfer_ack_received(self, ack):
        self.event_transfer_ack_received.set()
        self.speed_level = ack['speed_level']

    def on_transfer_nack_received(self, nack):
        self.speed_level = nack['speed_level']

    def on_disconnect_received(self):
        self.abort()

    def abort(self):
        self.state = self.STATE_DISCONNECTED
        self.event_connection_ack_received.set()
        self.event_connection_ack_received.clear()
        self.event_transfer_feedback.set()
        self.event_transfer_feedback.clear()
