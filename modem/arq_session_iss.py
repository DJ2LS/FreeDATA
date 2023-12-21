import threading
import data_frame_factory
import queue
import random
from codec2 import FREEDV_MODE
from modem_frametypes import FRAME_TYPE
import arq_session
import helpers
from enum import Enum

class ISS_State(Enum):
    NEW = 0
    OPEN_SENT = 1
    INFO_SENT = 2
    BURST_SENT = 3
    ENDED = 4
    FAILED = 5
    ABORTED = 6

class ARQSessionISS(arq_session.ARQSession):

    RETRIES_CONNECT = 10
    TIMEOUT_CONNECT_ACK = 3
    TIMEOUT_TRANSFER = 3

    STATE_TRANSITION = {
        ISS_State.OPEN_SENT: { 
            FRAME_TYPE.ARQ_SESSION_OPEN_ACK.value: 'send_info',
        },
        ISS_State.INFO_SENT: {
            FRAME_TYPE.ARQ_SESSION_OPEN_ACK.value: 'send_info',
            FRAME_TYPE.ARQ_SESSION_INFO_ACK.value: 'send_data',
        },
        ISS_State.BURST_SENT: {
            FRAME_TYPE.ARQ_SESSION_INFO_ACK.value: 'send_data',
            FRAME_TYPE.ARQ_BURST_ACK.value: 'send_data',
        },
        ISS_State.FAILED:{
            FRAME_TYPE.ARQ_STOP_ACK.value: 'transmission_failed'
        }
    }

    def __init__(self, config: dict, modem, dxcall: str, data: bytearray):
        super().__init__(config, modem, dxcall)
        self.data = data
        self.data_crc = ''

        self.confirmed_bytes = 0

        self.state = ISS_State.NEW
        self.id = self.generate_id()

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

    def generate_id(self):
        return random.randint(1,255)
    
    def transmit_wait_and_retry(self, frame_or_burst, timeout, retries, mode):
        while retries > 0 and not self.final:
            self.event_frame_received = threading.Event()
            if isinstance(frame_or_burst, list): burst = frame_or_burst
            else: burst = [frame_or_burst]
            for f in burst:
                self.transmit_frame(f, mode)
            self.event_frame_received.clear()
            self.log(f"Waiting {timeout} seconds...")
            if self.event_frame_received.wait(timeout):
                return
            self.log("Timeout!")
            retries = retries - 1
        self.set_state(ISS_State.FAILED)
        self.transmission_failed()

    def launch_twr(self, frame_or_burst, timeout, retries, mode):
        twr = threading.Thread(target = self.transmit_wait_and_retry, args=[frame_or_burst, timeout, retries, mode])
        twr.start()

    def start(self):
        session_open_frame = self.frame_factory.build_arq_session_open(self.dxcall, self.id)
        self.launch_twr(session_open_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.OPEN_SENT)

    def set_speed_and_frames_per_burst(self, frame):
        self.speed_level = frame['speed_level']
        self.log(f"Speed level set to {self.speed_level}")
        self.frames_per_burst = frame['frames_per_burst']
        self.log(f"Frames per burst set to {self.frames_per_burst}")

    def send_info(self, frame):
        info_frame = self.frame_factory.build_arq_session_info(self.id, len(self.data), 
                                                               helpers.get_crc_32(self.data), 
                                                               self.snr[0])

        self.launch_twr(info_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.INFO_SENT)

    def send_data(self, irs_frame):
        self.set_speed_and_frames_per_burst(irs_frame)

        if 'offset' in irs_frame:
            self.confirmed_bytes = irs_frame['offset']
            self.log(f"IRS confirmed {self.confirmed_bytes}/{len(self.data)} bytes")
            self.event_manager.send_arq_session_progress(
                True, self.id, self.dxcall, self.confirmed_bytes, len(self.data))

        if irs_frame["flag"]["FINAL"]:
            if self.confirmed_bytes == len(self.data) and irs_frame["flag"]["CHECKSUM"]:
                self.transmission_ended()
                return
            else:
                self.transmission_failed()
                return

        payload_size = self.get_data_payload_size()
        burst = []
        for f in range(0, self.frames_per_burst):
            offset = self.confirmed_bytes
            payload = self.data[offset : offset + payload_size]
            data_frame = self.frame_factory.build_arq_burst_frame(
                self.SPEED_LEVEL_DICT[self.speed_level]["mode"],
                self.id, self.confirmed_bytes, payload)
            burst.append(data_frame)
        self.launch_twr(burst, self.TIMEOUT_TRANSFER, self.RETRIES_CONNECT, mode='auto')
        self.set_state(ISS_State.BURST_SENT)

    def transmission_ended(self):
        self.set_state(ISS_State.ENDED)
        self.log("All data transfered!")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall, len(self.data),True)

    def transmission_failed(self):
        self.set_state(ISS_State.FAILED)
        self.log("Transmission failed!")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall, len(self.data),False)

    def stop_transmission(self):
        self.log(f"Stopping transmission...")
        stop_frame = self.frame_factory.build_arq_stop(self.id)
        self.launch_twr(stop_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.FAILED)
