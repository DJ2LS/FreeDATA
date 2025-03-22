import threading
import arq_session
import helpers
from modem_frametypes import FRAME_TYPE
from codec2 import FREEDV_MODE
from enum import Enum
import time


class IRS_State(Enum):
    """Enumeration representing the states of an IRS (Information Receiving Station) ARQ session.

    This enumeration defines the various states that an ARQ session on the
    Information Receiving Station (IRS) side can transition through during
    the data transfer process.

    Attributes:
        NEW: Initial state of a new session.
        OPEN_ACK_SENT: State after sending an acknowledgement to the session open request.
        INFO_ACK_SENT: State after sending an acknowledgement to the session information frame.
        BURST_REPLY_SENT: State after sending an acknowledgement to a burst data frame.
        ENDED: State after successfully receiving all data and confirming the checksum.
        FAILED: State after a session failure, such as a timeout or CRC mismatch.
        ABORTED: State after the session is explicitly aborted.
        RESUME: State allowing transmission resumption after a waiting period. This state is set after a period longer than TIMEOUT_DATA to ensure clean states.
    """
    NEW = 0
    OPEN_ACK_SENT = 1
    INFO_ACK_SENT = 2
    BURST_REPLY_SENT = 3
    ENDED = 4
    FAILED = 5
    ABORTED = 6
    RESUME = 7 # State, which allows resuming of a transmission - will be set after some waiting time, higher than TIMEOUT_DATA for ensuring clean states

class ARQSessionIRS(arq_session.ARQSession):
    """Manages an ARQ session on the Information Receiving Station (IRS) side.

    This class extends the base ARQSession class and implements the specific
    logic and state transitions for the IRS during an ARQ data transfer.
    """

    TIMEOUT_CONNECT = 55 #14.2
    TIMEOUT_DATA = 90

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
            #FRAME_TYPE.ARQ_SESSION_OPEN.value: 'send_open_ack',
        },
        IRS_State.ABORTED: {
            FRAME_TYPE.ARQ_STOP.value: 'send_stop_ack',
            #FRAME_TYPE.ARQ_SESSION_OPEN.value: 'send_open_ack',
            #FRAME_TYPE.ARQ_SESSION_INFO.value: 'send_info_ack',
            #FRAME_TYPE.ARQ_BURST_FRAME.value: 'receive_data',
        },
        IRS_State.RESUME: {
            FRAME_TYPE.ARQ_SESSION_OPEN.value: 'send_open_ack',
        }



    }

    def __init__(self, config: dict, modem, dxcall: str, session_id: int, state_manager):
        """Initializes a new ARQ session on the Information Receiving Station (IRS) side.

        This method initializes an ARQSessionIRS object, setting up the session
        parameters and state for the IRS. It inherits from the arq_session.ARQSession
        class and adds IRS-specific attributes.

        Args:
            config (dict): The configuration dictionary.
            modem: The modem object.
            dxcall (str): The DX call sign.
            session_id (int): The unique ID of the session.
            state_manager: The state manager object.
        """
        super().__init__(config, modem, dxcall, state_manager)

        self.id = session_id
        self.dxcall = dxcall
        self.version = 1
        self.is_IRS = True

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
        """Checks if all data has been received.

        This method compares the total expected length of the data with the
        number of bytes received so far.

        Returns:
            bool: True if all data has been received, False otherwise.
        """
        print(f"{self.total_length} vs {self.received_bytes}")
        return self.total_length == self.received_bytes

    def final_crc_matches(self) -> bool:
        """Checks if the final CRC matches the received data.

        This method calculates the CRC32 checksum of the received data and
        compares it with the expected CRC received from the sender.

        Returns:
            bool: True if the CRC matches, False otherwise.
        """
        return self.total_crc == helpers.get_crc_32(bytes(self.received_data)).hex()

    def transmit_and_wait(self, frame, timeout, mode):
        """Transmits a frame and waits for a response.

        This method transmits the given frame using the specified mode and waits
        for a response event within the given timeout period. If no response is
        received and the session is not aborted or failed, it logs a timeout
        message and calls the transmission_failed method.

        Args:
            frame: The frame to be transmitted.
            timeout: The timeout period in seconds.
            mode: The FreeDV mode to use for transmission.
        """
        self.event_frame_received.clear()
        self.transmit_frame(frame, mode)
        self.log(f"Waiting {timeout} seconds...")
        if not self.event_frame_received.wait(timeout) and self.state not in [IRS_State.ABORTED, IRS_State.FAILED]:
            self.log("Timeout waiting for ISS. Session failed.")
            self.transmission_failed()

    def launch_transmit_and_wait(self, frame, timeout, mode):
        """Launches the transmit_and_wait method in a separate thread.

        This method creates and starts a new daemon thread to execute the
        transmit_and_wait method, allowing the main thread to continue
        without blocking.

        Args:
            frame: The frame to be transmitted.
            timeout: The timeout period in seconds.
            mode: The FreeDV mode to use for transmission.
        """
        thread_wait = threading.Thread(target = self.transmit_and_wait, 
                                       args = [frame, timeout, mode], daemon=True)
        thread_wait.start()
    
    def send_open_ack(self, open_frame):
        """Sends an acknowledgement to the ARQ session open request.

        This method handles the reception of an ARQ_SESSION_OPEN frame.
        It negotiates the maximum transmission bandwidth, checks protocol
        version compatibility, and sends an ARQ_SESSION_OPEN_ACK frame.

        Args:
            open_frame: The received ARQ_SESSION_OPEN frame.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte as this method doesn't handle data.
        """
        # check for maximum bandwidth. If ISS bandwidth is higher than own, then use own
        if open_frame['maximum_bandwidth'] > self.config['MODEM']['maximum_bandwidth']:
            self.maximum_bandwidth = self.config['MODEM']['maximum_bandwidth']
        else:
            self.maximum_bandwidth = open_frame['maximum_bandwidth']
        self.log(f"Negotiated transmission bandwidth {self.maximum_bandwidth}Hz")

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
        """Sends an acknowledgement to the ARQ session information frame.

        This method handles the reception of an ARQ_SESSION_INFO frame.
        It extracts session details, calibrates speed settings, and sends
        an ARQ_SESSION_INFO_ACK frame.

        Args:
            info_frame: The received ARQ_SESSION_INFO frame.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte as this method doesn't handle data.
        """
        # Get session info from ISS
        if self.received_bytes == 0:
            self.received_data = bytearray(info_frame['total_length'])
        self.total_length = info_frame['total_length']
        self.total_crc = info_frame['total_crc']
        self.dx_snr.append(info_frame['snr'])
        self.type_byte = info_frame['type']

        self.calibrate_speed_settings()

        self.log(f"New transfer of {self.total_length} bytes, received_bytes: {self.received_bytes}")
        self.event_manager.send_arq_session_new(False, self.id, self.dxcall, self.total_length, self.state.name)

        info_ack = self.frame_factory.build_arq_session_info_ack(
            self.id, self.received_bytes, self.snr,
            self.speed_level, self.frames_per_burst, flag_abort=self.abort)
        self.launch_transmit_and_wait(info_ack, self.TIMEOUT_CONNECT, mode=FREEDV_MODE.signalling)
        if not self.abort:
            self.set_state(IRS_State.INFO_ACK_SENT)
        return None, None

    def process_incoming_data(self, frame):
        """Processes incoming data from a received frame.

        This method handles incoming data frames, checking for offset
        mismatches, extracting the relevant data portion, and updating the
        received data buffer. It also logs progress and sends ARQ session
        progress events.

        Args:
            frame: The received data frame.

        Returns:
            bool: True if the data was processed successfully, False otherwise.
        """
        if frame['offset'] != self.received_bytes:
            # TODO: IF WE HAVE AN OFFSET BECAUSE OF A SPEED LEVEL CHANGE FOR EXAMPLE,
            # TODO: WE HAVE TO DISCARD THE LAST BYTES, BUT NOT returning False!!
            # CASE: ACK is going lost.
            self.log(f"Discarding data offset: Offset = {frame['offset']} | Already received: {self.received_bytes}", isWarning=True)
            self.received_bytes = frame['offset']

            #return False

        remaining_data_length = self.total_length - self.received_bytes
        self.log(f"Remaining data: {remaining_data_length}", isWarning=True)
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
            False, self.id, self.dxcall, self.received_bytes, self.total_length, self.state.name, self.speed_level, self.calculate_session_statistics(self.received_bytes, self.total_length))

        return True

    def receive_data(self, burst_frame):
        """Receives and processes a burst data frame.

        This method processes the incoming burst data frame, sends acknowledgements,
        updates session state, and handles session completion or failure.

        Args:
            burst_frame: The received ARQ_BURST_FRAME.

        Returns:
            Tuple[bytearray, int]: The received data and its type byte if the transmission is successful,
                                    or None, None in case of failure or incomplete transmission.
        """
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
                                                         self.total_length, self.state.name, self.speed_level,
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
            self.transmit_frame(ack, mode=FREEDV_MODE.signalling_ack)
            self.log("CRC fail at the end of transmission!")
            return self.transmission_failed()


    def calibrate_speed_settings(self, burst_frame=None):
        """Calibrates the speed settings for the ARQ session based on SNR and bandwidth.

        This method determines the appropriate speed level for the session based on the
        current SNR and available bandwidth. It also sets the appropriate decode
        modes for the modem, ensuring smooth transitions between speed levels.

        Args:
            burst_frame (optional): The received burst frame, used to get the sender's speed level. Defaults to None.

        Returns:
            int: The calculated speed level.
        """
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
        #if appropriate_speed_level > self.speed_level and self.speed_level < len(self.SPEED_LEVEL_DICT) - 1:
        #    # we need to ensure, the received data is equal to our speed level before changing it
        #    if received_speed_level == self.speed_level:
        #        self.speed_level += 1
        #elif appropriate_speed_level < self.speed_level and self.speed_level > 0:
        #    #if received_speed_level == self.speed_level:
        #    #    self.speed_level -= 1

        # Always decode the current mode
        current_mode = self.get_mode_by_speed_level(self.speed_level).value
        modes_to_decode[current_mode] = True

        # Update previous speed level
        if self.previous_speed_level != self.speed_level:
            self.previous_speed_level = self.speed_level  # Update the previous speed level

        # Ensure, previous mode is decoded as well
        previous_mode = self.get_mode_by_speed_level(self.previous_speed_level).value
        modes_to_decode[previous_mode] = True

        # Ensure, appropriate mode is decoded as well
        appropriate_mode = self.get_mode_by_speed_level(appropriate_speed_level).value
        modes_to_decode[appropriate_mode] = True

        self.log(f"Modes to Decode: {list(modes_to_decode.keys())}", isWarning=True)
        # Apply the new decode mode based on the updated and previous speed levels
        self.modem.demodulator.set_decode_mode(modes_to_decode)

        # finally update the speed level to the appropriate one
        self.speed_level = appropriate_speed_level

        return self.speed_level

    def abort_transmission(self):
        """Aborts the ARQ transmission.

        This method sets the abort flag to True, signaling that the
        transmission should be terminated.
        """
        self.log("Aborting transmission... setting abort flag")
        self.abort = True

    def send_stop_ack(self, stop_frame):
        """Sends a stop acknowledgement and finalizes the session.

        This method handles the reception of an ARQ_STOP frame by sending an
        ARQ_STOP_ACK, setting the session state to ABORTED, and sending session
        finished events. It also pushes session statistics if enabled.

        Args:
            stop_frame: The received ARQ_STOP frame.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte as this method doesn't handle data.
        """
        stop_ack = self.frame_factory.build_arq_stop_ack(self.id)
        self.launch_transmit_and_wait(stop_ack, self.TIMEOUT_CONNECT, mode=FREEDV_MODE.signalling_ack)
        self.set_state(IRS_State.ABORTED)
        self.states.setARQ(False)
        session_stats = self.calculate_session_statistics(self.received_bytes, self.total_length)

        self.event_manager.send_arq_session_finished(
                False, self.id, self.dxcall, False, self.state.name, statistics=session_stats)
        if self.config['STATION']['enable_stats']:
            self.statistics.push(self.state.name, session_stats, self.dxcall)

        return None, None

    def transmission_failed(self, irs_frame=None):
        """Handles transmission failures.

        This method is called when a transmission fails. It sets the session
        state to FAILED, logs the failure, sends session finished events,
        pushes session statistics if enabled, and disables ARQ.

        Args:
            irs_frame (optional): The received IRS frame. Defaults to None.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte.
        """
        # final function for failed transmissions
        self.session_ended = time.time()
        self.set_state(IRS_State.FAILED)
        self.log("Transmission failed!")
        #self.modem.demodulator.set_decode_mode()
        session_stats = self.calculate_session_statistics(self.received_bytes, self.total_length)

        self.event_manager.send_arq_session_finished(True, self.id, self.dxcall,False, self.state.name, statistics=session_stats)
        if self.config['STATION']['enable_stats']:
            self.statistics.push(self.state.name, session_stats, self.dxcall)

        self.states.setARQ(False)
        return None, None

    def transmission_aborted(self):
        """Handles the abortion of the transmission.

        This method is called when the transmission is aborted. It sets the
        session state to ABORTED, logs the abortion, sends session finished
        events, and disables ARQ.

        Returns:
            Tuple[None, None]: Returns None for both data and type_byte.
        """
        if self.state not in [IRS_State.ABORTED, IRS_State.ENDED]:
            self.log("session aborted")
            self.session_ended = time.time()
            self.set_state(IRS_State.ABORTED)
            # break actual retries
            self.event_frame_received.set()


            #self.modem.demodulator.set_decode_mode()
            self.event_manager.send_arq_session_finished(
                True, self.id, self.dxcall, False, self.state.name, statistics=self.calculate_session_statistics(self.received_bytes, self.total_length))
            self.states.setARQ(False)
        return None, None