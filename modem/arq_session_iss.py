import threading
import data_frame_factory
import queue
import random
from codec2 import FREEDV_MODE
from modem_frametypes import FRAME_TYPE
import arq_session
import helpers
from enum import Enum
import time

class ISS_State(Enum):
    NEW = 0
    OPEN_SENT = 1
    INFO_SENT = 2
    BURST_SENT = 3
    ENDED = 4
    FAILED = 5
    ABORTING = 6 # state while running abort sequence and waiting for stop ack
    ABORTED = 7 # stop ack received

class ARQSessionISS(arq_session.ARQSession):

    RETRIES_CONNECT = 10

    # DJ2LS: 3 seconds seems to be too small for radios with a too slow PTT toggle time
    # DJ2LS: 3.5 seconds is working well WITHOUT a channel busy detection delay
    TIMEOUT_CHANNEL_BUSY = 2
    TIMEOUT_CONNECT_ACK = 3.5 + TIMEOUT_CHANNEL_BUSY
    TIMEOUT_TRANSFER = 3.5 + TIMEOUT_CHANNEL_BUSY
    TIMEOUT_STOP_ACK = 3.5 + TIMEOUT_CHANNEL_BUSY

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
            FRAME_TYPE.ARQ_STOP_ACK.value: 'transmission_aborted'
        },
        ISS_State.ABORTING: {
            FRAME_TYPE.ARQ_STOP_ACK.value: 'transmission_aborted',
        },
        ISS_State.ABORTED: {
            FRAME_TYPE.ARQ_STOP_ACK.value: 'transmission_aborted',
        }
    }

    def __init__(self, config: dict, modem, dxcall: str, state_manager, data: bytearray, type_byte: bytes):
        super().__init__(config, modem, dxcall)
        self.state_manager = state_manager
        self.data = data
        self.total_length = len(data)
        self.data_crc = ''
        self.type_byte = type_byte
        self.confirmed_bytes = 0

        self.state = ISS_State.NEW
        self.state_enum = ISS_State # needed for access State enum from outside
        self.id = self.generate_id()

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

        self.speed_level = 0

    def generate_id(self):
        while True:
            random_int = random.randint(1,255)
            if random_int not in self.state_manager.arq_iss_sessions:
                return random_int
            if len(self.state_manager.arq_iss_sessions) >= 255:
                return False


    def transmit_wait_and_retry(self, frame_or_burst, timeout, retries, mode):
        while retries > 0:
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
        twr = threading.Thread(target = self.transmit_wait_and_retry, args=[frame_or_burst, timeout, retries, mode], daemon=True)
        twr.start()

    def start(self):
        self.event_manager.send_arq_session_new(
            True, self.id, self.dxcall, self.total_length, self.state.name)
        session_open_frame = self.frame_factory.build_arq_session_open(self.dxcall, self.id)
        self.launch_twr(session_open_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.OPEN_SENT)

    def update_speed_level(self, frame):
        self.log("---------------------------------------------------------", isWarning=True)

        # Log the received frame for debugging
        self.log(f"Received frame: {frame}", isWarning=True)

        # Safely extract upshift and downshift flags with default to False if not present
        upshift = frame['flag'].get('UPSHIFT', False)
        downshift = frame['flag'].get('DOWNSHIFT', False)

        # Check for UPSHIFT frame and ensure speed level does not exceed max limit
        if upshift and not downshift and self.speed_level < len(self.SPEED_LEVEL_DICT) - 1:
            self.speed_level += 1
            self.log(f"Upshifting. New speed level: {self.speed_level}")

        # Check for DOWNSHIFT frame and ensure speed level does not go below 0
        elif downshift and not upshift and self.speed_level > 0:
            self.speed_level -= 1
            self.log(f"Downshifting. New speed level: {self.speed_level}")



    def send_info(self, irs_frame):
        # check if we received an abort flag
        if irs_frame["flag"]["ABORT"]:
            self.transmission_aborted(irs_frame)
            return

        info_frame = self.frame_factory.build_arq_session_info(self.id, self.total_length,
                                                               helpers.get_crc_32(self.data), 
                                                               self.snr[0], self.type_byte)

        self.launch_twr(info_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.INFO_SENT)

        return None, None

    def send_data(self, irs_frame):

        self.update_speed_level(irs_frame)

        if 'offset' in irs_frame:
            self.confirmed_bytes = irs_frame['offset']
            self.log(f"IRS confirmed {self.confirmed_bytes}/{self.total_length} bytes")
            self.event_manager.send_arq_session_progress(
                True, self.id, self.dxcall, self.confirmed_bytes, self.total_length, self.state.name)

        # check if we received an abort flag
        if irs_frame["flag"]["ABORT"]:
            self.transmission_aborted(irs_frame)
            return None, None

        if irs_frame["flag"]["FINAL"]:
            if self.confirmed_bytes == self.total_length and irs_frame["flag"]["CHECKSUM"]:
                self.transmission_ended(irs_frame)

            else:
                self.transmission_failed()
            return None, None

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
        return None, None

    def transmission_ended(self, irs_frame):
        # final function for sucessfully ended transmissions
        self.session_ended = time.time()
        self.set_state(ISS_State.ENDED)
        self.log(f"All data transfered! flag_final={irs_frame['flag']['FINAL']}, flag_checksum={irs_frame['flag']['CHECKSUM']}")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,True, self.state.name, statistics=self.calculate_session_statistics())
        self.state_manager.remove_arq_iss_session(self.id)
        self.states.setARQ(False)
        self.arq_data_type_handler.transmitted(self.type_byte, self.data)
        return None, None

    def transmission_failed(self, irs_frame=None):
        # final function for failed transmissions
        self.session_ended = time.time()
        self.set_state(ISS_State.FAILED)
        self.log(f"Transmission failed!")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,False, self.state.name, statistics=self.calculate_session_statistics())
        self.states.setARQ(False)

        self.arq_data_type_handler.failed(self.type_byte, self.data)
        return None, None

    def abort_transmission(self, irs_frame=None):
        # function for starting the abort sequence
        self.log(f"aborting transmission...")
        self.set_state(ISS_State.ABORTING)

        self.event_manager.send_arq_session_finished(
            True, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics())

        # break actual retries
        self.event_frame_received.set()

        # start with abort sequence
        self.send_stop()

    def send_stop(self):
        stop_frame = self.frame_factory.build_arq_stop(self.id)
        self.launch_twr(stop_frame, self.TIMEOUT_STOP_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)

    def transmission_aborted(self, irs_frame):
        self.log("session aborted")
        self.session_ended = time.time()
        self.set_state(ISS_State.ABORTED)
        # break actual retries
        self.event_frame_received.set()

        self.event_manager.send_arq_session_finished(
            True, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics())
        self.state_manager.remove_arq_iss_session(self.id)
        self.states.setARQ(False)
        return None, None

