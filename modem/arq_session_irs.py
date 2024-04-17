import threading
import arq_session
import helpers
from modem_frametypes import FRAME_TYPE
from codec2 import FREEDV_MODE
from enum import Enum
import time

class IRS_State(Enum):
    NEW = 0
    OPEN_ACK_SENT = 1
    INFO_ACK_SENT = 2
    BURST_REPLY_SENT = 3
    ENDED = 4
    FAILED = 5
    ABORTED = 6

class ARQSessionIRS(arq_session.ARQSession):

    TIMEOUT_CONNECT = 55 #14.2
    TIMEOUT_DATA = 120

    STATE_TRANSITION = {
        IRS_State.NEW: { 
            FRAME_TYPE.ARQ_SESSION_OPEN.value : 'send_open_ack',
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack'
        },
        IRS_State.OPEN_ACK_SENT: { 
            FRAME_TYPE.ARQ_SESSION_OPEN.value: 'send_open_ack',
            FRAME_TYPE.ARQ_SESSION_INFO.value: 'send_info_ack',
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack'

        },
        IRS_State.INFO_ACK_SENT: {
            FRAME_TYPE.ARQ_SESSION_INFO.value: 'send_info_ack',
            FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack'

        },
        IRS_State.BURST_REPLY_SENT: {
            FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack'

        },
        IRS_State.ENDED: {
            FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack'

        },
        IRS_State.FAILED: {
            FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack'
        },
        IRS_State.ABORTED: {
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack',
            FRAME_TYPE.ARQ_SESSION_OPEN.value: 'send_open_ack',
            FRAME_TYPE.ARQ_SESSION_INFO.value: 'send_info_ack',
            FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
        },
    }

    def __init__(self, config: dict, modem, dxcall: str, session_id: int, state_manager):
        super().__init__(config, modem, dxcall, state_manager)

        self.id = session_id
        self.dxcall = dxcall
        self.version = 1

        self.state = IRS_State.NEW
        self.state_enum = IRS_State  # needed for access State enum from outside

        self.type_byte = None
        self.total_length = 0
        self.total_crc = ''
        self.received_data = None
        self.received_bytes = 0
        self.received_crc = None

        self.maximum_bandwidth = 0

        self.abort = False

    def all_data_received(self):
        print(f"{self.total_length} vs {self.received_bytes}")
        return self.total_length == self.received_bytes

    def final_crc_matches(self) -> bool:
        return self.total_crc == helpers.get_crc_32(bytes(self.received_data)).hex()

    def transmit_and_wait(self, frame, timeout, mode):
        self.event_frame_received.clear()
        self.transmit_frame(frame, mode)
        self.log(f"Waiting {timeout} seconds...")
        if not self.event_frame_received.wait(timeout):
            self.log("Timeout waiting for ISS. Session failed.")
            self.transmission_failed()

    def launch_transmit_and_wait(self, frame, timeout, mode):
        thread_wait = threading.Thread(target = self.transmit_and_wait, 
                                       args = [frame, timeout, mode], daemon=True)
        thread_wait.start()
    
    def send_open_ack(self, open_frame):
        self.maximum_bandwidth = open_frame['maximum_bandwidth']
        # check for maximum bandwidth. If ISS bandwidth is higher than own, then use own
        if open_frame['maximum_bandwidth'] > self.config['MODEM']['maximum_bandwidth']:
            self.maximum_bandwidth = self.config['MODEM']['maximum_bandwidth']


        self.event_manager.send_arq_session_new(
            False, self.id, self.dxcall, 0, self.state.name)

        if open_frame['protocol_version'] not in [self.protocol_version]:
            self.abort = True
            self.log(f"Protocol version mismatch! Setting disconnect flag!", isWarning=True)
            self.set_state(IRS_State.ABORTED)

        ack_frame = self.frame_factory.build_arq_session_open_ack(
            self.id,
            self.dxcall, 
            self.version,
            self.snr, flag_abort=self.abort)

        self.launch_transmit_and_wait(ack_frame, self.TIMEOUT_CONNECT, mode=FREEDV_MODE.signalling)
        if not self.abort:
            self.set_state(IRS_State.OPEN_ACK_SENT)
        return None, None

    def send_info_ack(self, info_frame):
        # Get session info from ISS
        self.received_data = bytearray(info_frame['total_length'])
        self.total_length = info_frame['total_length']
        self.total_crc = info_frame['total_crc']
        self.dx_snr.append(info_frame['snr'])
        self.type_byte = info_frame['type']

        self.calibrate_speed_settings()

        self.log(f"New transfer of {self.total_length} bytes")
        self.event_manager.send_arq_session_new(False, self.id, self.dxcall, self.total_length, self.state.name)

        info_ack = self.frame_factory.build_arq_session_info_ack(
            self.id, self.total_crc, self.snr,
            self.speed_level, self.frames_per_burst, flag_abort=self.abort)
        self.launch_transmit_and_wait(info_ack, self.TIMEOUT_CONNECT, mode=FREEDV_MODE.signalling)
        if not self.abort:
            self.set_state(IRS_State.INFO_ACK_SENT)
        return None, None

    def process_incoming_data(self, frame):
        print(frame)
        if frame['offset'] != self.received_bytes:
            # TODO: IF WE HAVE AN OFFSET BECAUSE OF A SPEED LEVEL CHANGE FOR EXAMPLE,
            # TODO: WE HAVE TO DISCARD THE LAST BYTES, BUT NOT returning False!!
            self.log(f"Discarding data offset {frame['offset']} vs {self.received_bytes}", isWarning=True)
            #return False

        remaining_data_length = self.total_length - self.received_bytes
        # Is this the last data part?
        if remaining_data_length <= len(frame['data']):
            # we only want the remaining length, not the entire frame data
            data_part = frame['data'][:remaining_data_length]
        else:
            # we want the entire frame data
            data_part = frame['data']

        self.received_data[frame['offset']:] = data_part
        #self.received_bytes += len(data_part)
        self.received_bytes = len(self.received_data)
        self.log(f"Received {self.received_bytes}/{self.total_length} bytes")
        self.event_manager.send_arq_session_progress(
            False, self.id, self.dxcall, self.received_bytes, self.total_length, self.state.name, self.calculate_session_statistics(self.received_bytes, self.total_length))

        return True

    def receive_data(self, burst_frame):
        self.process_incoming_data(burst_frame)
        # update statistics
        self.update_histograms(self.received_bytes, self.total_length)
        
        if not self.all_data_received():
            self.calibrate_speed_settings(burst_frame=burst_frame)
            ack = self.frame_factory.build_arq_burst_ack(
                self.id,
                self.speed_level,
                flag_abort=self.abort
            )

            self.set_state(IRS_State.BURST_REPLY_SENT)
            self.event_manager.send_arq_session_progress(False, self.id, self.dxcall, self.received_bytes,
                                                         self.total_length, self.state.name,
                                                         statistics=self.calculate_session_statistics(
                                                             self.received_bytes, self.total_length))

            self.launch_transmit_and_wait(ack, self.TIMEOUT_DATA, mode=FREEDV_MODE.signalling_ack)
            return None, None

        if self.final_crc_matches():
            self.log("All data received successfully!")
            ack = self.frame_factory.build_arq_burst_ack(self.id,
                                                         self.speed_level,
                                                         flag_final=True,
                                                         flag_checksum=True)
            self.transmit_frame(ack, mode=FREEDV_MODE.signalling_ack)
            self.log("ACK sent")
            self.session_ended = time.time()
            self.set_state(IRS_State.ENDED)

            return self.received_data, self.type_byte
        else:

            ack = self.frame_factory.build_arq_burst_ack(self.id,
                                                         self.speed_level,
                                                         flag_final=True,
                                                         flag_checksum=False)
            self.transmit_frame(ack, mode=FREEDV_MODE.signalling)
            self.log("CRC fail at the end of transmission!")
            return self.transmission_failed()

    def calibrate_speed_settings(self, burst_frame=None):
        if burst_frame:
            received_speed_level = burst_frame['speed_level']
        else:
            received_speed_level = 0

        latest_snr = self.snr if self.snr else -10
        appropriate_speed_level = self.get_appropriate_speed_level(latest_snr, self.maximum_bandwidth)
        modes_to_decode = {}

        # Log the latest SNR, current, appropriate speed levels, and the previous speed level
        self.log(
            f"Latest SNR: {latest_snr}, Current Speed Level: {self.speed_level}, Appropriate Speed Level: {appropriate_speed_level}, Previous Speed Level: {self.previous_speed_level}",
            isWarning=True)

        # Adjust the speed level by one step towards the appropriate level, if needed
        if appropriate_speed_level > self.speed_level and self.speed_level < len(self.SPEED_LEVEL_DICT) - 1:
            # we need to ensure, the received data is equal to our speed level before changing it
            if received_speed_level == self.speed_level:
                self.speed_level += 1
        elif appropriate_speed_level < self.speed_level and self.speed_level > 0:
            # we need to ensure, the received data is equal to our speed level before changing it
            if received_speed_level == self.speed_level:
                self.speed_level -= 1

        # Always decode the current mode
        current_mode = self.get_mode_by_speed_level(self.speed_level).value
        modes_to_decode[current_mode] = True

        # Decode the previous speed level mode
        if self.previous_speed_level != self.speed_level:
            previous_mode = self.get_mode_by_speed_level(self.previous_speed_level).value
            modes_to_decode[previous_mode] = True
            self.previous_speed_level = self.speed_level  # Update the previous speed level

        self.log(f"Modes to Decode: {list(modes_to_decode.keys())}", isWarning=True)
        # Apply the new decode mode based on the updated and previous speed levels
        self.modem.demodulator.set_decode_mode(modes_to_decode)

        return self.speed_level

    def abort_transmission(self):
        self.log("Aborting transmission... setting abort flag")
        self.abort = True

    def send_stop_ack(self, stop_frame):
        stop_ack = self.frame_factory.build_arq_stop_ack(self.id)
        self.launch_transmit_and_wait(stop_ack, self.TIMEOUT_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(IRS_State.ABORTED)
        self.states.setARQ(False)
        self.event_manager.send_arq_session_finished(
                False, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics(self.received_bytes, self.total_length))
        return None, None

    def transmission_failed(self, irs_frame=None):
        # final function for failed transmissions
        self.session_ended = time.time()
        self.set_state(IRS_State.FAILED)
        self.log("Transmission failed!")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,False, self.state.name, statistics=self.calculate_session_statistics(self.received_bytes, self.total_length))
        self.states.setARQ(False)
        return None, None
