import threading
import data_frame_factory
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
    TIMEOUT_CHANNEL_BUSY = 0
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
        super().__init__(config, modem, dxcall, state_manager)
        self.state_manager = state_manager
        self.data = data
        self.total_length = len(data)
        self.data_crc = ''
        self.type_byte = type_byte
        self.confirmed_bytes = 0
        self.expected_byte_offset = 0

        self.state = ISS_State.NEW
        self.state_enum = ISS_State # needed for access State enum from outside
        self.id = self.generate_id()

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

    def generate_id(self):
        while True:
            random_int = random.randint(1,255)
            if random_int not in self.state_manager.arq_iss_sessions:
                return random_int
            if len(self.state_manager.arq_iss_sessions) >= 255:
                return False

    def transmit_wait_and_retry(self, frame_or_burst, timeout, retries, mode, isARQBurst=False, ):
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

            # TODO TEMPORARY TEST FOR SENDING IN LOWER SPEED LEVEL IF WE HAVE TWO FAILED TRANSMISSIONS!!!
            if retries == 8 and isARQBurst and self.speed_level > 0:
                self.log("SENDING IN FALLBACK SPEED LEVEL", isWarning=True)
                self.speed_level = 0
                print(f" CONFIRMED BYTES: {self.confirmed_bytes}")
                self.send_data({'flag':{'ABORT': False, 'FINAL': False}, 'speed_level': self.speed_level}, fallback=True)

                return

        self.set_state(ISS_State.FAILED)
        self.transmission_failed()

    def launch_twr(self, frame_or_burst, timeout, retries, mode, isARQBurst=False):
        twr = threading.Thread(target = self.transmit_wait_and_retry, args=[frame_or_burst, timeout, retries, mode, isARQBurst], daemon=True)
        twr.start()

    def start(self):
        maximum_bandwidth = self.config['MODEM']['maximum_bandwidth']
        print(maximum_bandwidth)
        self.event_manager.send_arq_session_new(
            True, self.id, self.dxcall, self.total_length, self.state.name)
        session_open_frame = self.frame_factory.build_arq_session_open(self.dxcall, self.id, maximum_bandwidth, self.protocol_version)
        self.launch_twr(session_open_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.OPEN_SENT)

    def update_speed_level(self, frame):
        self.log("---------------------------------------------------------", isWarning=True)

        # Log the received frame for debugging
        self.log(f"Received frame: {frame}", isWarning=True)

        # Extract the speed_level directly from the frame
        if 'speed_level' in frame:
            new_speed_level = frame['speed_level']
            # Ensure the new speed level is within the allowable range
            if 0 <= new_speed_level < len(self.SPEED_LEVEL_DICT):
                # Log the speed level change if it's different from the current speed level
                if new_speed_level != self.speed_level:
                    self.log(f"Changing speed level from {self.speed_level} to {new_speed_level}", isWarning=True)
                    self.speed_level = new_speed_level  # Update the current speed level
                else:
                    self.log("Received speed level is the same as the current speed level.", isWarning=True)
            else:
                self.log(f"Received speed level {new_speed_level} is out of allowable range.", isWarning=True)
        else:
            self.log("No speed level specified in the received frame.", isWarning=True)

    def send_info(self, irs_frame):
        # check if we received an abort flag
        if irs_frame["flag"]["ABORT"]:
            return self.transmission_aborted(irs_frame)

        info_frame = self.frame_factory.build_arq_session_info(self.id, self.total_length,
                                                               helpers.get_crc_32(self.data), 
                                                               self.snr, self.type_byte)

        self.launch_twr(info_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.INFO_SENT)

        return None, None

    def send_data(self, irs_frame, fallback=None):

        # interrupt transmission when aborting
        if self.state in [ISS_State.ABORTED, ISS_State.ABORTING]:
            self.event_frame_received.set()
            self.send_stop()
            return

        # update statistics
        self.update_histograms(self.confirmed_bytes, self.total_length)
        self.update_speed_level(irs_frame)


        if self.expected_byte_offset > self.total_length:
            self.confirmed_bytes = self.total_length
        elif not fallback:
            self.confirmed_bytes = self.expected_byte_offset

        self.log(f"IRS confirmed {self.confirmed_bytes}/{self.total_length} bytes")
        self.event_manager.send_arq_session_progress(True, self.id, self.dxcall, self.confirmed_bytes, self.total_length, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))

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
        for _ in range(0, self.frames_per_burst):
            offset = self.confirmed_bytes
            #self.expected_byte_offset = offset
            payload = self.data[offset : offset + payload_size]
            #self.expected_byte_offset = offset + payload_size
            self.expected_byte_offset = offset + len(payload)
            #print(f"EXPECTED----------------------{self.expected_byte_offset}")
            data_frame = self.frame_factory.build_arq_burst_frame(
                self.SPEED_LEVEL_DICT[self.speed_level]["mode"],
                self.id, offset, payload, self.speed_level)
            burst.append(data_frame)
        self.launch_twr(burst, self.TIMEOUT_TRANSFER, self.RETRIES_CONNECT, mode='auto', isARQBurst=True)
        self.set_state(ISS_State.BURST_SENT)
        return None, None

    def transmission_ended(self, irs_frame):
        # final function for sucessfully ended transmissions
        self.session_ended = time.time()
        self.set_state(ISS_State.ENDED)
        self.log(f"All data transfered! flag_final={irs_frame['flag']['FINAL']}, flag_checksum={irs_frame['flag']['CHECKSUM']}")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,True, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))

        #print(self.state_manager.p2p_connection_sessions)
        #print(self.arq_data_type_handler.state_manager.p2p_connection_sessions)

        self.arq_data_type_handler.transmitted(self.type_byte, self.data, self.calculate_session_statistics(self.confirmed_bytes, self.total_length))
        self.state_manager.remove_arq_iss_session(self.id)
        self.states.setARQ(False)
        return None, None

    def transmission_failed(self, irs_frame=None):
        # final function for failed transmissions
        self.session_ended = time.time()
        self.set_state(ISS_State.FAILED)
        self.log("Transmission failed!")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,False, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))
        self.states.setARQ(False)

        self.arq_data_type_handler.failed(self.type_byte, self.data, self.calculate_session_statistics(self.confirmed_bytes, self.total_length))
        return None, None

    def abort_transmission(self, irs_frame=None):
        # function for starting the abort sequence
        self.log("aborting transmission...")
        self.set_state(ISS_State.ABORTING)

        self.event_manager.send_arq_session_finished(
            True, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))

        # break actual retries
        self.event_frame_received.set()

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
            True, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))
        self.state_manager.remove_arq_iss_session(self.id)
        self.states.setARQ(False)
        return None, None

