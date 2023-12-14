import threading
import data_frame_factory
import queue
import arq_session
import helpers
from modem_frametypes import FRAME_TYPE

class ARQSessionIRS(arq_session.ARQSession):

    STATE_NEW = 0
    STATE_OPEN_ACK_SENT = 1
    STATE_INFO_ACK_SENT = 2
    STATE_BURST_REPLY_SENT = 3
    STATE_ENDED = 4
    STATE_FAILED = 5

    RETRIES_CONNECT = 3
    RETRIES_TRANSFER = 3 # we need to increase this

    TIMEOUT_CONNECT = 6
    TIMEOUT_DATA = 6

    STATE_TRANSITION = {
        STATE_NEW: { 
            FRAME_TYPE.ARQ_SESSION_OPEN.value : 'send_open_ack',
        },
        STATE_OPEN_ACK_SENT: { 
            FRAME_TYPE.ARQ_SESSION_OPEN.value: 'send_open_ack',
            FRAME_TYPE.ARQ_SESSION_INFO.value: 'send_info_ack',
        },
        STATE_INFO_ACK_SENT: {
            FRAME_TYPE.ARQ_SESSION_INFO.value: 'send_info_ack',
            FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
        },
        STATE_BURST_REPLY_SENT: {
            FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
        },
    }

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str, session_id: int):
        super().__init__(config, tx_frame_queue, dxcall)

        self.id = session_id
        self.dxcall = dxcall
        self.version = 1

        self.state = self.STATE_NEW

        self.total_length = 0
        self.total_crc = ''
        self.received_data = None
        self.received_bytes = 0
        self.received_crc = None

        self.transmitted_acks = 0

    def set_modem_decode_modes(self, modes):
        pass

    def all_data_received(self):
        return self.received_bytes == len(self.received_data)

    def final_crc_check(self):
        return self.total_crc == helpers.get_crc_32(bytes(self.received_data)).hex()

    def transmit_and_wait(self, frame, timeout):
        self.transmit_frame(frame)
        self.log(f"Waiting {timeout} seconds...")
        if not self.event_frame_received.wait(timeout):
            # use case: data burst got lost, we want to send a NACK with updated speed level
            if self.state in [self.STATE_BURST_REPLY_SENT, self.STATE_INFO_ACK_SENT]:
                self.transmitted_acks = 0
                self.calibrate_speed_settings()
                self.send_burst_nack()
                return

            self.log("Timeout waiting for ISS. Session failed.")
            self.set_state(self.STATE_FAILED)

    def launch_transmit_and_wait(self, frame, timeout):
        thread_wait = threading.Thread(target = self.transmit_and_wait, 
                                       args = [frame, timeout])
        thread_wait.start()
    
    def send_open_ack(self, open_frame):
        ack_frame = self.frame_factory.build_arq_session_open_ack(
            self.id,
            self.dxcall, 
            self.version,
            self.snr[0])
        self.launch_transmit_and_wait(ack_frame, self.TIMEOUT_CONNECT)
        self.set_state(self.STATE_OPEN_ACK_SENT)

    def send_info_ack(self, info_frame):
        # Get session info from ISS
        self.received_data = bytearray(info_frame['total_length'])
        self.total_crc = info_frame['total_crc']
        self.dx_snr.append(info_frame['snr'])

        info_ack = self.frame_factory.build_arq_session_info_ack(
            self.id, self.total_crc, self.snr[0],
            self.speed_level, self.frames_per_burst)
        self.launch_transmit_and_wait(info_ack, self.TIMEOUT_CONNECT)
        self.set_state(self.STATE_INFO_ACK_SENT)

    def send_burst_nack(self):
        self.calibrate_speed_settings()
        nack = self.frame_factory.build_arq_burst_ack(self.id, self.received_bytes, self.speed_level, self.frames_per_burst, self.snr[0])
        self.transmit_and_wait(nack)


    def process_incoming_data(self, frame):
        if frame['offset'] != self.received_bytes:
            self.logger.info(f"Discarding data frame due to wrong offset", frame=self.frame_received)
            return False

        remaining_data_length = len(self.received_data) - self.received_bytes

        # Is this the last data part?
        if remaining_data_length <= len(frame['data']):
            # we only want the remaining length, not the entire frame data
            data_part = frame['data'][:remaining_data_length]
        else:
            # we want the entire frame data
            data_part = frame['data']

        self.received_data[frame['offset']:] = data_part
        self.received_bytes += len(data_part)

        return True

    def receive_data(self, burst_frame):
        self.process_incoming_data(burst_frame)
        self.calibrate_speed_settings()
        ack = self.frame_factory.build_arq_burst_ack(
            self.id, self.received_bytes, 
            self.speed_level, self.frames_per_burst, self.snr[0])

        if not self.all_data_received():
            # increase ack counter
            self.transmitted_acks += 1
            self.transmit_and_wait(ack)
            self.set_state(self.STATE_BURST_REPLY_SENT)
            return

        if self.final_crc_check():
            self.log("All data received successfully!")
            self.transmit_frame(ack)
            self.set_state(self.STATE_ENDED)

        else:
            self.log("CRC fail at the end of transmission!")
            self.set_state(self.STATE_FAILED)

    def calibrate_speed_settings(self):
        # if we have two ACKS, then consider increasing speed level
        if self.transmitted_acks >= 2:
            self.transmitted_acks = 0
            new_speed_level = min(self.speed_level + 1, len(self.SPEED_LEVEL_DICT) - 1)

            # check first if the next mode supports the actual snr
            if self.snr >= self.SPEED_LEVEL_DICT[new_speed_level]["min_snr"]:
                self.speed_level = new_speed_level

