import threading
import data_frame_factory
import queue
import random
from codec2 import FREEDV_MODE
from modem_frametypes import FRAME_TYPE
import arq_session
import helpers

class ARQSessionISS(arq_session.ARQSession):

    STATE_NEW = 0
    STATE_OPEN_SENT = 1
    STATE_INFO_SENT = 2
    STATE_BURST_SENT = 3
    STATE_ENDED = 4
    STATE_FAILED = 5

    RETRIES_CONNECT = 3
    RETRIES_TRANSFER = 3

    TIMEOUT_CONNECT_ACK = 5
    TIMEOUT_TRANSFER = 2

    STATE_TRANSITION = {
        STATE_OPEN_SENT: { 
            FRAME_TYPE.ARQ_SESSION_OPEN_ACK.value: 'send_info',
        },
        STATE_INFO_SENT: {
            FRAME_TYPE.ARQ_SESSION_OPEN_ACK.value: 'send_info',
            FRAME_TYPE.ARQ_SESSION_INFO_ACK.value: 'send_data',
        },
        STATE_BURST_SENT: {
            FRAME_TYPE.ARQ_SESSION_INFO_ACK.value: 'send_data',
            FRAME_TYPE.ARQ_BURST_ACK.value: 'send_data',
            FRAME_TYPE.ARQ_BURST_NACK.value: 'send_data',
        },
    }

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str, data: bytearray):
        super().__init__(config, tx_frame_queue, dxcall)
        self.data = data
        self.data_crc = ''

        self.confirmed_bytes = 0

        self.state = self.STATE_NEW
        self.id = self.generate_id()

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

    def generate_id(self):
        return random.randint(1,255)
    
    def transmit_wait_and_retry(self, frame_or_burst, timeout, retries):
        while retries > 0:
            if isinstance(frame_or_burst, list): burst = frame_or_burst
            else: burst = [frame_or_burst]
            for f in burst:
                self.transmit_frame(f)
            self.log(f"Waiting {timeout} seconds...")
            if self.event_frame_received.wait(timeout):
                return
            self.log("Timeout!")
            retries = retries - 1
        self.set_state(self.STATE_FAILED)
        self.log("Session failed")

    def launch_twr(self, frame_or_burst, timeout, retries):
        twr = threading.Thread(target = self.transmit_wait_and_retry, args=[frame_or_burst, timeout, retries])
        twr.start()

    def start(self):
        session_open_frame = self.frame_factory.build_arq_session_open(self.dxcall, self.id)
        self.launch_twr(session_open_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT)
        self.set_state(self.STATE_OPEN_SENT)

    def set_speed_and_frames_per_burst(self, frame):
        self.speed_level = frame['speed_level']
        self.log(f"Speed level set to {self.speed_level}")
        self.frames_per_burst = frame['frames_per_burst']
        self.log(f"Frames per burst set to {self.frames_per_burst}")

    def send_info(self, open_ack_frame):
        info_frame = self.frame_factory.build_arq_session_info(self.id, len(self.data), 
                                                               helpers.get_crc_32(self.data), 
                                                               self.snr[0])
        self.launch_twr(info_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT)
        self.set_state(self.STATE_INFO_SENT)

    def send_data(self, irs_frame):
        self.set_speed_and_frames_per_burst(irs_frame)

        if 'offset' in irs_frame:
            self.confirmed_bytes = irs_frame['offset']

        if self.confirmed_bytes == len(self.data):
            self.set_state(self.STATE_ENDED)
            self.log("All data transfered!")
            return

        payload_size = self.get_data_payload_size()
        burst = []
        for f in range(0, self.frames_per_burst):
            offset = self.confirmed_bytes
            payload = self.data[offset : offset + payload_size]
            data_frame = self.frame_factory.build_arq_burst_frame(
                self.MODE_BY_SPEED[self.speed_level],
                self.id, self.confirmed_bytes, payload)
            burst.append(data_frame)

        self.launch_twr(burst, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT)
        self.set_state(self.STATE_BURST_SENT)
