import threading
import data_frame_factory
import random
from codec2 import FREEDV_MODE
from modem_frametypes import FRAME_TYPE
import arq_session
import helpers
from enum import Enum
import time
import stats

class ISS_State(Enum):
    """Enumeration representing the states of an ISS (Information Sending Station) ARQ session.

    This enumeration defines the various states that an ARQ session on the
    Information Sending Station (ISS) side can transition through during
    the data transfer process.

    Attributes:
        NEW: Initial state of a new session.
        OPEN_SENT: State after sending an ARQ session open request.
        INFO_SENT: State after sending the session information frame.
        BURST_SENT: State after sending a burst data frame.
        ENDED: State after successfully transmitting all data and receiving confirmation.
        FAILED: State after a session failure, such as a timeout or abort.
        ABORTING: State while running the abort sequence and waiting for a stop acknowledgement.
        ABORTED: State after receiving a stop acknowledgement, indicating session termination.
    """
    NEW = 0
    OPEN_SENT = 1
    INFO_SENT = 2
    BURST_SENT = 3
    ENDED = 4
    FAILED = 5
    ABORTING = 6 # state while running abort sequence and waiting for stop ack
    ABORTED = 7 # stop ack received

class ARQSessionISS(arq_session.ARQSession):
    """Manages an ARQ session on the Information Sending Station (ISS) side.

    This class extends the base ARQSession and handles the transmission of data
    using the ARQ protocol. It manages session state, retries, timeouts, and
    data transfer.
    """

    RETRIES_CONNECT = 5
    RETRIES_INFO = 10
    RETRIES_DATA = 25
    RETRIES_STOP = 5

    # DJ2LS: 3 seconds seems to be too small for radios with a too slow PTT toggle time
    # DJ2LS: 3.5 seconds is working well WITHOUT a channel busy detection delay
    TIMEOUT_CHANNEL_BUSY = 0
    TIMEOUT_CONNECT_ACK = 4.5 + TIMEOUT_CHANNEL_BUSY
    TIMEOUT_TRANSFER = 3.5 + TIMEOUT_CHANNEL_BUSY
    TIMEOUT_STOP_ACK = 4.5 + TIMEOUT_CHANNEL_BUSY

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
        """Initializes a new ARQ session on the Information Sending Station (ISS) side.

        This method sets up the ARQ session for the ISS, initializing session
        parameters, data, CRC, state, and frame factory. It also enables the
        decoder for signalling ACK bursts.

        Args:
            config (dict): The configuration dictionary.
            modem: The modem object.
            dxcall (str): The DX call sign.
            state_manager: The state manager object.
            data (bytearray): The data to be transmitted.
            type_byte (bytes): The type byte of the data.
        """
        super().__init__(config, modem, dxcall, state_manager)
        self.state_manager = state_manager
        self.data = data
        self.total_length = len(data)
        self.data_crc = helpers.get_crc_32(self.data)
        self.type_byte = type_byte
        self.confirmed_bytes = 0
        self.expected_byte_offset = 0

        self.state = ISS_State.NEW
        self.state_enum = ISS_State # needed for access State enum from outside
        self.id = self.generate_id()

        self.is_IRS = False

        # enable decoder for signalling ACK bursts
        self.modem.demodulator.set_decode_mode(modes_to_decode=None, is_arq_irs=False)

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

    def generate_id(self):
        """Generates a unique session ID.

        This method attempts to generate a unique 8-bit session ID. It first
        checks for existing sessions with matching CRC to allow resuming
        interrupted transmissions. If no match is found, it generates a new
        ID based on the data CRC and ensures it's not already in use.

        Returns:
            int: The generated session ID (1-255), or False if all IDs are exhausted.
        """
        # Iterate through existing sessions to find a matching CRC
        for session_id, session_data in self.state_manager.arq_iss_sessions.items():
            if session_data.data_crc == self.data_crc and session_data.state in [ISS_State.FAILED, ISS_State.ABORTED]:
                # If a matching CRC is found, use this session ID
                self.log(f"Matching CRC found, deleting existing session and resuming transmission", isWarning=True)
                self.states.remove_arq_iss_session(session_id)
                return session_id
        self.log(f"No matching CRC found, creating new session id", isWarning=False)

        # Compute 8-bit integer from the 32-bit CRC
        # Convert the byte sequence to a 32-bit integer (little-endian)
        checksum_int = int.from_bytes(self.data_crc, byteorder='little')
        random_int = checksum_int % 256

        # Check if the generated 8-bit integer can be used
        if random_int not in self.state_manager.arq_iss_sessions:
            return random_int

        # If the generated ID is already used, generate a new random ID
        while True:
            random_int = random.randint(1, 255)
            if random_int not in self.state_manager.arq_iss_sessions:
                return random_int
            if len(self.state_manager.arq_iss_sessions) >= 255:
                # Return False if all possible session IDs are exhausted
                return False

    def transmit_wait_and_retry(self, frame_or_burst, timeout, retries, mode, isARQBurst=False):
        """Transmits a frame or burst, waits for a response, and retries if necessary.

        This method transmits the given frame or burst of frames, waits for a
        response event, and retries the transmission if a timeout occurs.
        It handles retries up to the specified limit and implements a fallback
        mechanism for ARQ bursts by switching to a lower speed level if
        necessary.

        Args:
            frame_or_burst: The frame or list of frames to be transmitted.
            timeout (float): The timeout period in seconds.
            retries (int): The maximum number of retries.
            mode: The FreeDV mode to use for transmission.
            isARQBurst (bool, optional): True if transmitting an ARQ burst, False otherwise. Defaults to False.
        """
        while retries > 0 and self.state not in [ISS_State.ABORTED, ISS_State.ABORTING]:
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
            if retries == self.RETRIES_DATA - 2 and isARQBurst and self.speed_level > 0 and self.state not in [ISS_State.ABORTED, ISS_State.ABORTING]:
                self.log("SENDING IN FALLBACK SPEED LEVEL", isWarning=True)
                self.speed_level = 0
                print(f" CONFIRMED BYTES: {self.confirmed_bytes}")
                self.send_data({'flag':{'ABORT': False, 'FINAL': False}, 'speed_level': self.speed_level}, fallback=True)

                return

        self.set_state(ISS_State.FAILED)
        self.transmission_failed()

    def launch_twr(self, frame_or_burst, timeout, retries, mode, isARQBurst=False):
        """Launches the transmit_wait_and_retry method in a separate thread.

        Creates and starts a daemon thread to execute the transmit_wait_and_retry
        method. This allows the transmission and retry process to occur in the
        background without blocking the main thread.

        Args:
            frame_or_burst: The frame or burst of frames to transmit.
            timeout (float): The timeout for each transmission attempt.
            retries (int): The number of transmission retries to attempt.
            mode: The FreeDV mode to use for transmission.
            isARQBurst (bool, optional): True if the transmission is an ARQ burst, False otherwise. Defaults to False.
        """
        twr = threading.Thread(target = self.transmit_wait_and_retry, args=[frame_or_burst, timeout, retries, mode, isARQBurst], daemon=True)
        twr.start()

    def start(self):
        """Starts the ARQ session.

        This method initiates the ARQ session by sending a session open frame
        to the IRS and setting the session state to OPEN_SENT. It also sends
        an ARQ session new event.
        """
        maximum_bandwidth = self.config['MODEM']['maximum_bandwidth']
        print(maximum_bandwidth)
        self.event_manager.send_arq_session_new(
            True, self.id, self.dxcall, self.total_length, self.state.name)
        session_open_frame = self.frame_factory.build_arq_session_open(self.dxcall, self.id, maximum_bandwidth, self.protocol_version)
        self.launch_twr(session_open_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.OPEN_SENT)

    def update_speed_level(self, frame):
        """Updates the transmission speed level based on the received frame.

        This method extracts the speed level from the received frame and updates
        the session's speed level accordingly. It logs the speed level change
        and handles cases where the received speed level is outside the
        allowable range.

        Args:
            frame: The received frame containing the new speed level.
        """
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
        """Sends the session information frame to the IRS.

        This method builds and sends the ARQ_SESSION_INFO frame containing
        details about the data to be transmitted, such as total length, CRC,
        SNR, and data type. It also handles transmission retries and aborts
        based on the received IRS frame.

        Args:
            irs_frame: The received frame from the IRS.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte as this method doesn't handle data.
        """
        # check if we received an abort flag
        if irs_frame["flag"]["ABORT"]:
            return self.transmission_aborted(irs_frame=irs_frame)

        info_frame = self.frame_factory.build_arq_session_info(self.id, self.total_length,
                                                               self.data_crc,
                                                               self.snr, self.type_byte)

        self.launch_twr(info_frame, self.TIMEOUT_CONNECT_ACK, self.RETRIES_INFO, mode=FREEDV_MODE.signalling)
        self.set_state(ISS_State.INFO_SENT)

        return None, None

    def send_data(self, irs_frame, fallback=None):
        """Sends data bursts to the IRS.

        This method handles sending data bursts to the IRS, managing speed
        level adjustments, acknowledgements, and session progress updates.
        It also handles transmission aborts and session completion or failure.

        Args:
            irs_frame: The received frame from the IRS.
            fallback (bool, optional): Indicates if this is a fallback transmission attempt at a lower speed level. Defaults to None.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte as this method doesn't handle data directly.
        """
        if 'offset' in irs_frame:
            self.log(f"received data offset: {irs_frame['offset']}", isWarning=True)
            self.expected_byte_offset = irs_frame['offset']

        # interrupt transmission when aborting
        if self.state in [ISS_State.ABORTED, ISS_State.ABORTING]:
            #self.event_frame_received.set()
            #self.send_stop()
            return

        # update statistics
        self.update_histograms(self.confirmed_bytes, self.total_length)
        self.update_speed_level(irs_frame)

        if self.expected_byte_offset > self.total_length:
            self.confirmed_bytes = self.total_length
        elif not fallback:
            self.confirmed_bytes = self.expected_byte_offset

        self.log(f"IRS confirmed {self.confirmed_bytes}/{self.total_length} bytes")
        self.event_manager.send_arq_session_progress(True, self.id, self.dxcall, self.confirmed_bytes, self.total_length, self.state.name, self.speed_level, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))

        # check if we received an abort flag
        if irs_frame["flag"]["ABORT"]:
            self.transmission_aborted(irs_frame=irs_frame)
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
        self.launch_twr(burst, self.TIMEOUT_TRANSFER, self.RETRIES_DATA, mode='auto', isARQBurst=True)
        self.set_state(ISS_State.BURST_SENT)
        return None, None

    def transmission_ended(self, irs_frame):
        """Handles the successful completion of the transmission.

        This method is called when the transmission ends successfully. It sets
        the session state to ENDED, logs the completion, sends session finished
        events, transmits session statistics, and cleans up the session.

        Args:
            irs_frame: The received IRS frame.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte.
        """
        # final function for sucessfully ended transmissions
        self.session_ended = time.time()
        self.set_state(ISS_State.ENDED)
        self.log(f"All data transfered! flag_final={irs_frame['flag']['FINAL']}, flag_checksum={irs_frame['flag']['CHECKSUM']}")
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,True, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))

        #print(self.state_manager.p2p_connection_sessions)
        #print(self.arq_data_type_handler.state_manager.p2p_connection_sessions)
        session_stats = self.calculate_session_statistics(self.confirmed_bytes, self.total_length)
        self.arq_data_type_handler.transmitted(self.type_byte, self.data, session_stats)

        self.state_manager.remove_arq_iss_session(self.id)
        self.states.setARQ(False)
        return None, None

    def transmission_failed(self, irs_frame=None):
        """Handles transmission failures.

        This method is called when a transmission fails. It sets the session
        state to FAILED, logs the failure, sends session finished events,
        and disables ARQ. It also notifies the ARQ data type handler about
        the failure.

        Args:
            irs_frame (optional): The received IRS frame, if any. Defaults to None.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte.
        """
        # final function for failed transmissions
        self.session_ended = time.time()
        self.set_state(ISS_State.FAILED)
        self.log("Transmission failed!")
        session_stats=self.calculate_session_statistics(self.confirmed_bytes, self.total_length)
        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,False, self.state.name, session_stats)

        self.states.setARQ(False)

        self.arq_data_type_handler.failed(self.type_byte, self.data, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))
        return None, None

    def abort_transmission(self, send_stop=False, irs_frame=None):
        """Starts the ARQ transmission abort sequence.

        This method initiates the abort sequence, sets the session state to
        ABORTING, sends session finished events, clears the audio output queue,
        and optionally sends a stop frame after a delay.

        Args:
            send_stop (bool, optional): Whether to send an ARQ_STOP frame. Defaults to False.
            irs_frame (optional): The received IRS frame, if any. Defaults to None.
        """
        self.log("aborting transmission...")
        self.set_state(ISS_State.ABORTING)

        self.event_manager.send_arq_session_finished(
            True, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))

        # clear audio out queue
        self.modem.audio_out_queue.queue.clear()

        # break actual retries
        self.event_frame_received.set()

        # wait for transmit function to be ready before setting event
        while self.states.isTransmitting():
            threading.Event().wait(0.100)

        # break actual retries
        self.event_frame_received.set()

        if send_stop:
            # sleep some time for avoiding packet collission
            threading.Event().wait(self.TIMEOUT_STOP_ACK)
            self.send_stop()

        self.states.setARQ(False)

    def send_stop(self):
        """Sends an ARQ stop frame.

        This method builds and sends an ARQ_STOP frame to the IRS, initiating
        the termination of the ARQ session. It uses the launch_twr method
        for transmission and retries.
        """
        stop_frame = self.frame_factory.build_arq_stop(self.id)
        self.launch_twr(stop_frame, self.TIMEOUT_STOP_ACK, self.RETRIES_STOP, mode=FREEDV_MODE.signalling)

    def transmission_aborted(self, irs_frame=None):
        """Handles the abortion of the transmission.

        This method is called when the transmission is aborted. It sets the
        session state to ABORTED, logs the abortion, sends session finished
        events, and disables ARQ.

        Args:
            irs_frame (optional): The received IRS frame, if any. Defaults to None.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte.
        """

        # Only run this part, if we are not already aborted or ended the session.
        if self.state not in [ISS_State.ABORTED, ISS_State.ENDED]:
            self.log("session aborted")
            self.session_ended = time.time()
            self.set_state(ISS_State.ABORTED)
            # break actual retries
            self.event_frame_received.set()

            self.event_manager.send_arq_session_finished(
                True, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics(self.confirmed_bytes, self.total_length))
            #self.state_manager.remove_arq_iss_session(self.id)
            self.states.setARQ(False)
        return None, None
