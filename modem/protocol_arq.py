
import threading
import time
import codec2
import helpers
import modem
import stats
import structlog
from codec2 import FREEDV_MODE, FREEDV_MODE_USED_SLOTS
from modem_frametypes import FRAME_TYPE as FR_TYPE
import event_manager

from data_handler import DATA
TESTMODE = False
class ARQ:
    def __init__(self, config, event_queue, states):
        super().__init__(config, event_queue, states)

        self.log = structlog.get_logger("DHARQ")
        self.event_queue = event_queue
        self.states = states
        self.event_manager = event_manager.EventManager([event_queue])


        # ARQ PROTOCOL VERSION
        # v.5 - signalling frame uses datac0
        # v.6 - signalling frame uses datac13
        # v.7 - adjusting ARQ timeout
        # v.8 - adjusting ARQ structure
        self.arq_protocol_version = 8

        self.stats = stats.stats(config, event_queue, states)

        # load config
        self.mycallsign = config['STATION']['mycall']
        self.myssid = config['STATION']['myssid']
        self.mycallsign += "-" + str(self.myssid)
        encoded_call = helpers.callsign_to_bytes(self.mycallsign)
        self.mycallsign = helpers.bytes_to_callsign(encoded_call)
        self.ssid_list = config['STATION']['ssid_list']
        self.mycallsign_crc = helpers.get_crc_24(self.mycallsign)
        self.mygrid = config['STATION']['mygrid']
        self.enable_fsk = config['MODEM']['enable_fsk']
        self.respond_to_cq = config['MODEM']['respond_to_cq']
        self.enable_hmac = config['MODEM']['enable_hmac']
        self.enable_stats = config['STATION']['enable_stats']
        self.enable_morse_identifier = config['MODEM']['enable_morse_identifier']
        self.arq_rx_buffer_size = config['MODEM']['rx_buffer_size']
        self.enable_experimental_features = False
        # flag to indicate if modem running in low bandwidth mode
        self.low_bandwidth_mode = config["MODEM"]["enable_low_bandwidth_mode"]

        # Enable general responding to channel openers for example
        # this can be combined with a callsign blacklist for example
        self.respond_to_call = True


        self.modem_frequency_offset = 0

        self.dxcallsign = b"ZZ9YY-0"
        self.dxcallsign_crc = b''
        self.dxgrid = b''

        # length of signalling frame
        self.length_sig0_frame = 14
        self.length_sig1_frame = 14

        # duration of frames
        self.duration_datac4 = 5.17
        self.duration_datac13 = 2.0
        self.duration_datac1 = 4.18
        self.duration_datac3 = 3.19
        self.duration_sig0_frame = self.duration_datac13
        self.duration_sig1_frame = self.duration_datac13
        self.longest_duration = self.duration_datac4

        # hold session id
        self.session_id = bytes(1)

        # ------- ARQ SESSION
        self.arq_file_transfer = False
        self.IS_ARQ_SESSION_MASTER = False
        self.arq_session_last_received = 0
        self.arq_session_timeout = 30
        self.session_connect_max_retries = 10

        self.arq_compression_factor = 0

        self.transmission_uuid = ""

        self.burst_last_received = 0.0  # time of last "live sign" of a burst
        self.data_channel_last_received = 0.0  # time of last "live sign" of a frame

        # Flag to indicate if we received an ACK frame for a burst
        self.burst_ack = False
        # Flag to indicate if we received an ACK frame for a data frame
        self.data_frame_ack_received = False
        # Flag to indicate if we received a request for repeater frames
        self.rpt_request_received = False
        self.rpt_request_buffer = []  # requested frames, saved in a list
        self.burst_rpt_counter = 0


        # 3 bytes for the BOF Beginning of File indicator in a data frame
        self.data_frame_bof = b"BOF"
        # 3 bytes for the EOF End of File indicator in a data frame
        self.data_frame_eof = b"EOF"





        self.n_retries_per_burst = 0
        self.max_n_frames_per_burst = 1

        # Flag to indicate if we received a low bandwidth mode channel opener
        self.received_LOW_BANDWIDTH_MODE = False


        self.data_channel_max_retries = 15

        # event for checking arq_state_event
        self.arq_state_event = threading.Event()
        # -------------- AVAILABLE MODES START-----------
        # IMPORTANT: LISTS MUST BE OF EQUAL LENGTH

        # --------------------- LOW BANDWIDTH

        # List of codec2 modes to use in "low bandwidth" mode.
        self.mode_list_low_bw = [
            FREEDV_MODE.datac4.value,
        ]
        # List for minimum SNR operating level for the corresponding mode in self.mode_list
        self.snr_list_low_bw = [-100]
        # List for time to wait for corresponding mode in seconds
        self.time_list_low_bw = [self.duration_datac4]

        # --------------------- HIGH BANDWIDTH

        # List of codec2 modes to use in "high bandwidth" mode.
        self.mode_list_high_bw = [
            FREEDV_MODE.datac4.value,
            FREEDV_MODE.datac3.value,
            FREEDV_MODE.datac1.value,
        ]
        # List for minimum SNR operating level for the corresponding mode in self.mode_list
        self.snr_list_high_bw = [-100, 0, 3]
        # List for time to wait for corresponding mode in seconds
        # test with 6,7 --> caused sometimes a frame timeout if ack frame takes longer
        # TODO Need to check why ACK frames needs more time
        # TODO Adjust these times
        self.time_list_high_bw = [self.duration_datac4, self.duration_datac3, self.duration_datac1]
        # -------------- AVAILABLE MODES END-----------

        # Mode list for selecting between low bandwidth ( 500Hz ) and modes with higher bandwidth
        # but ability to fall back to low bandwidth modes if needed.
        if self.low_bandwidth_mode:
            # List of codec2 modes to use in "low bandwidth" mode.
            self.mode_list = self.mode_list_low_bw
            # list of times to wait for corresponding mode in seconds
            self.time_list = self.time_list_low_bw

        else:
            # List of codec2 modes to use in "high bandwidth" mode.
            self.mode_list = self.mode_list_high_bw
            # list of times to wait for corresponding mode in seconds
            self.time_list = self.time_list_high_bw

        self.speed_level = len(self.mode_list) - 1  # speed level for selecting mode
        self.states.set("arq_speed_level", self.speed_level)


        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_nack_counter = 0
        self.frame_received_counter = 0


        # TIMEOUTS
        self.transmission_timeout = 180  # transmission timeout in seconds
        self.channel_busy_timeout = 3  # time how long we want to wait until channel busy state overrides






        # START THE THREAD FOR THE TIMEOUT WATCHDOG
        watchdog_thread = threading.Thread(
            target=self.watchdog, name="watchdog", daemon=True
        )
        watchdog_thread.start()

        arq_session_thread = threading.Thread(
            target=self.heartbeat, name="watchdog", daemon=True
        )
        arq_session_thread.start()

    def send_ident_frame(self, transmit) -> None:
        """Build and send IDENT frame """
        ident_frame = bytearray(self.length_sig1_frame)
        ident_frame[:1] = bytes([FR_TYPE.IDENT.value])
        ident_frame[1:self.length_sig1_frame] = self.mycallsign

        # Transmit frame
        if transmit:
            self.enqueue_frame_for_tx([ident_frame], c2_mode=FREEDV_MODE.sig0.value)
        else:
            return ident_frame

    def send_disconnect_frame(self) -> None:
        """Build and send a disconnect frame"""
        disconnection_frame = bytearray(self.length_sig1_frame)
        disconnection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_CLOSE.value])
        disconnection_frame[1:2] = self.session_id
        disconnection_frame[2:5] = self.dxcallsign_crc

        # wait if  we have a channel busy condition
        if self.states.channel_busy:
            self.channel_busy_handler()

        self.enqueue_frame_for_tx([disconnection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=3, repeat_delay=0)


    def check_if_mode_fits_to_busy_slot(self):
        """
        Check if actual mode is fitting into given busy state

        Returns:

        """
        mode_name = FREEDV_MODE(self.mode_list[self.speed_level]).name
        mode_slots = FREEDV_MODE_USED_SLOTS[mode_name].value
        if mode_slots in [self.states.channel_busy_slot]:
            self.log.warning(
                "[Modem] busy slot detection",
                slots=self.states.channel_busy_slot,
                mode_slots=mode_slots,
            )
            return False
        return True

    def arq_calculate_speed_level(self, snr):
        current_speed_level = self.speed_level
        self.frame_received_counter += 1
        # try increasing speed level only if we had two successful decodes
        if self.frame_received_counter >= 2:
            self.frame_received_counter = 0

            # make sure new speed level isn't higher than available modes
            new_speed_level = min(self.speed_level + 1, len(self.mode_list) - 1)
            # check if actual snr is higher than minimum snr for next mode
            if snr >= self.snr_list[new_speed_level]:
                self.speed_level = new_speed_level


            else:
                self.log.info("[Modem] ARQ | increasing speed level not possible because of SNR limit",
                              given_snr=snr,
                              needed_snr=self.snr_list[new_speed_level]
                              )

            # calculate if speed level fits to busy condition
            if not self.check_if_mode_fits_to_busy_slot():
                self.speed_level = current_speed_level

            self.states.set("arq_speed_level", self.speed_level)

        # Update modes we are listening to
        self.set_listening_modes(False, True, self.mode_list[self.speed_level])

        self.log.debug(
            "[Modem] calculated speed level",
            speed_level=self.speed_level,
            given_snr=snr,
            min_snr=self.snr_list[self.speed_level],
        )






        # for i in range(0, 6, 2):
        #    if not missing_area[i: i + 2].endswith(b"\x00\x00"):
        #        self.rpt_request_buffer.insert(0, missing_area[i: i + 2])





    ##########################################################################################################
    # ARQ DATA CHANNEL HANDLER
    ##########################################################################################################





    def stop_transmission(self) -> None:
        """
        Force a stop of the running transmission
        """
        self.log.warning("[Modem] Stopping transmission!")

        self.event_manager.send_custom_event(
            freedata="modem-message",
            arq="transmission",
            status="stopped",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8')
        )

        stop_frame = bytearray(self.length_sig0_frame)
        stop_frame[:1] = bytes([FR_TYPE.ARQ_STOP.value])
        stop_frame[1:4] = self.dxcallsign_crc
        stop_frame[4:7] = self.mycallsign_crc
        # TODO Not sure if we really need the session id when disconnecting
        # stop_frame[1:2] = self.session_id
        stop_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)
        self.enqueue_frame_for_tx([stop_frame], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)

        self.arq_cleanup()

    def received_stop_transmission(
            self, deconstructed_frame: list
    ) -> None:  # pylint: disable=unused-argument
        """
        Received a transmission stop
        """
        self.log.warning("[Modem] Stopping transmission!")
        self.states.set("is_modem_busy", False)
        self.states.set("is_arq_state", False)
        self.event_manager.send_custom_event(
            freedata="modem-message",
            arq="transmission",
            status="stopped",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            uuid=self.transmission_uuid
        )
        self.arq_cleanup()

    def channel_busy_handler(self):
        """
        function for handling the channel busy situation
        Args:

        Returns:
        """
        self.log.warning("[Modem] Channel busy, waiting until free...")
        self.event_manager.send_custom_event(
            freedata="modem-message",
            channel="busy",
            status="waiting",
        )

        # wait while timeout not reached and our busy state is busy
        channel_busy_timeout = time.time() + self.channel_busy_timeout
        while self.states.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
            threading.Event().wait(0.01)

    # ------------ CALCULATE TRANSFER RATES


    def reset_statistics(self) -> None:
        """
        Reset statistics
        """
        # reset ARQ statistics
        self.states.set("bytes_per_minute_burst", 0)
        self.states.set("arq_total_bytes", 0)
        self.states.set("self.states.arq_seconds_until_finish", 0)
        self.states.set("arq_bits_per_second", 0)
        self.states.set("bytes_per_minute", 0)
        self.states.set("arq_transmission_percent", 0)
        self.states.set("arq_compression_factor", 0)


    # ----------------------CLEANUP AND RESET FUNCTIONS
    def arq_cleanup(self) -> None:
        """
        Cleanup function which clears all ARQ states
        """

        # TODO
        # We need to check if we are in a ARQ session
        # Then we cant delete the session_id for now
        self.states.delete_arq_instance_by_id(self.session_id)


        if TESTMODE:
            self.log.debug("[Modem] TESTMODE: arq_cleanup: Not performing cleanup.")
            return

        self.log.debug("[Modem] arq_cleanup")
        # wait a second for smoother arq behaviour
        helpers.wait(1.0)

        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False
        self.burst_ack = False
        self.rpt_request_received = False
        self.burst_rpt_counter = 0
        self.data_frame_ack_received = False
        self.arq_rx_burst_buffer = []
        self.arq_rx_frame_buffer = b""
        self.burst_ack_snr = 0
        self.arq_burst_last_payload = 0
        self.rx_n_frame_of_burst = 0
        self.rx_n_frames_per_burst = 0

        # reset modem receiving state to reduce cpu load
        modem.RECEIVE_SIG0 = True
        modem.RECEIVE_SIG1 = False
        modem.RECEIVE_DATAC1 = False
        modem.RECEIVE_DATAC3 = False
        modem.RECEIVE_DATAC4 = False
        # modem.RECEIVE_FSK_LDPC_0 = False
        modem.RECEIVE_FSK_LDPC_1 = False

        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_nack_counter = 0
        self.frame_received_counter = 0
        self.speed_level = len(self.mode_list) - 1
        self.states.set("arq_speed_level", self.speed_level)

        # low bandwidth mode indicator
        self.received_LOW_BANDWIDTH_MODE = False

        # reset retry counter for rx channel / burst
        self.n_retries_per_burst = 0

        # reset max retries possibly overriden by api
        self.session_connect_max_retries = 10
        self.data_channel_max_retries = 10

        self.states.set("arq_session_state", "disconnected")
        self.states.arq_speed_list = []
        self.states.set("is_arq_state", False)
        self.arq_state_event = threading.Event()
        self.arq_file_transfer = False

        self.beacon_paused = False
        # reset beacon interval timer for not directly starting beacon after ARQ
        self.beacon_interval_timer = time.time() + self.beacon_interval

    def arq_reset_ack(self, state: bool) -> None:
        """
        Funktion for resetting acknowledge states
        Args:
          state:bool:

        """
        self.burst_ack = state
        self.rpt_request_received = state
        self.data_frame_ack_received = state

    def set_listening_modes(self, enable_sig0: bool, enable_sig1: bool, mode: int) -> None:
        # sourcery skip: extract-duplicate-method
        """
        Function for setting the data modes we are listening to for saving cpu power

        Args:
          enable_sig0:int: Enable/Disable signalling mode 0
          enable_sig1:int: Enable/Disable signalling mode 1
          mode:int: Codec2 mode to listen for

        """
        # set modes we want to listen to
        modem.RECEIVE_SIG0 = enable_sig0
        modem.RECEIVE_SIG1 = enable_sig1

        if mode == codec2.FREEDV_MODE.datac1.value:
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_DATAC4 = False
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[Modem] Changing listening data mode", mode="datac1")
        elif mode == codec2.FREEDV_MODE.datac3.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = True
            modem.RECEIVE_DATAC4 = False
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[Modem] Changing listening data mode", mode="datac3")
        elif mode == codec2.FREEDV_MODE.datac4.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_DATAC4 = True
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[Modem] Changing listening data mode", mode="datac4")
        elif mode == codec2.FREEDV_MODE.fsk_ldpc_1.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_DATAC4 = False
            modem.RECEIVE_FSK_LDPC_1 = True
            self.log.debug("[Modem] Changing listening data mode", mode="fsk_ldpc_1")
        else:
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = True
            modem.RECEIVE_DATAC4 = True
            modem.RECEIVE_FSK_LDPC_1 = True
            self.log.debug(
                "[Modem] Changing listening data mode", mode="datac1/datac3/fsk_ldpc"
            )

    # ------------------------- WATCHDOG FUNCTIONS FOR TIMER
    def watchdog(self) -> None:
        """Author: DJ2LS

        Watchdog master function. From here, "pet" the watchdogs

        """
        while True:
            threading.Event().wait(0.1)
            self.data_channel_keep_alive_watchdog()
            self.burst_watchdog()
            self.arq_session_keep_alive_watchdog()

    def burst_watchdog(self) -> None:
        """
        Watchdog which checks if we are running into a connection timeout
        DATA BURST
        """
        # IRS SIDE
        # TODO We need to redesign this part for cleaner state handling
        # Return if not ARQ STATE and not ARQ SESSION STATE as they are different use cases
        if (
                not self.states.is_arq_state
                and self.states.arq_session_state != "connected"
                or not self.is_IRS
        ):
            return

        # get modem error state
        modem_error_state = modem.get_modem_error_state()

        # We want to reach this state only if connected ( == return above not called )
        if self.rx_n_frames_per_burst > 1:
            # uses case for IRS: reduce time for waiting by counting "None" in burst buffer
            frames_left = self.arq_rx_burst_buffer.count(None)
        elif self.rx_n_frame_of_burst == 0 and self.rx_n_frames_per_burst == 0:
            # use case for IRS: We didn't receive a burst yet, because the first one got lost
            # in this case we don't have any information about the expected burst length
            # we must assume, we are getting a burst with max_n_frames_per_burst
            frames_left = self.max_n_frames_per_burst
        else:
            frames_left = 1

        # make sure we don't have a 0 here for avoiding too short timeouts
        if frames_left == 0:
            frames_left = 1

        # timeout is reached, if we didnt receive data, while we waited
        # for the corresponding data frame + the transmitted signalling frame of ack/nack
        # + a small offset of about 1 second
        timeout = \
            (
                    self.burst_last_received
                    + (self.time_list[self.speed_level] * frames_left)
                    + self.duration_sig0_frame
                    + self.channel_busy_timeout
                    + 1
            )

        # override calculation
        # if we reached 2/3 of the waiting time and didnt received a signal
        # then send NACK earlier
        time_left = timeout - time.time()
        waiting_time = (self.time_list[
                            self.speed_level] * frames_left) + self.duration_sig0_frame + self.channel_busy_timeout + 1
        timeout_percent = 100 - (time_left / waiting_time * 100)
        # timeout_percent = 0
        if timeout_percent >= 75 and not self.states.is_codec2_traffic and not self.states.isTransmitting():
            override = True
        else:
            override = False

        # TODO Enable this for development
        print(
            f"timeout expected in:{round(timeout - time.time())} | timeout percent: {timeout_percent} | frames left: {frames_left} of {self.rx_n_frames_per_burst} | speed level: {self.speed_level}")
        # if timeout is expired, but we are receivingt codec2 data,
        # better wait some more time because data might be important for us
        # reason for this situation can be delays on IRS and ISS, maybe because both had a busy channel condition.
        # Nevertheless, we need to keep timeouts short for efficiency
        if timeout <= time.time() or modem_error_state and not self.states.is_codec2_traffic and not self.states.isTransmitting() or override:
            self.log.warning(
                "[Modem] Burst decoding error or timeout",
                attempt=self.n_retries_per_burst,
                max_attempts=self.rx_n_max_retries_per_burst,
                speed_level=self.speed_level,
                modem_error_state=modem_error_state
            )

            print(
                f"frames_per_burst {self.rx_n_frame_of_burst} / {self.rx_n_frames_per_burst}, Repeats: {self.burst_rpt_counter} Nones: {self.arq_rx_burst_buffer.count(None)}")
            # check if we have N frames per burst > 1
            if self.rx_n_frames_per_burst > 1 and self.burst_rpt_counter < 3 and self.arq_rx_burst_buffer.count(
                    None) > 0:
                # reset self.burst_last_received
                self.burst_last_received = time.time() + self.time_list[self.speed_level] * frames_left
                self.burst_rpt_counter += 1
                self.send_retransmit_request_frame()

            else:

                # reset self.burst_last_received counter
                self.burst_last_received = time.time()

                # reduce speed level if nack counter increased
                self.frame_received_counter = 0
                self.burst_nack_counter += 1
                if self.burst_nack_counter >= 2:
                    self.burst_nack_counter = 0
                    self.speed_level = max(self.speed_level - 1, 0)
                    self.states.set("arq_speed_level", self.speed_level)

                # TODO Create better mechanisms for handling n frames per burst for bad channels
                # reduce frames per burst
                if self.burst_rpt_counter >= 2:
                    tx_n_frames_per_burst = max(self.rx_n_frames_per_burst - 1, 1)
                else:
                    tx_n_frames_per_burst = self.rx_n_frames_per_burst

                # Update modes we are listening to
                self.set_listening_modes(True, True, self.mode_list[self.speed_level])

                # TODO Does SNR make sense for NACK if we dont have an actual SNR information?
                self.send_burst_nack_frame_watchdog(tx_n_frames_per_burst)

                # Update data_channel timestamp
                # TODO Disabled this one for testing.
                # self.data_channel_last_received = time.time()
                self.n_retries_per_burst += 1
        else:
            # debugging output
            # print((self.data_channel_last_received + self.time_list[self.speed_level])-time.time())
            pass

        if self.n_retries_per_burst >= self.rx_n_max_retries_per_burst:
            self.stop_transmission()

    def data_channel_keep_alive_watchdog(self) -> None:
        """
        watchdog which checks if we are running into a connection timeout
        DATA CHANNEL
        """
        # and not static.ARQ_SEND_KEEP_ALIVE:
        if self.states.is_arq_state and self.states.is_modem_busy:
            threading.Event().wait(0.01)
            if (
                    self.data_channel_last_received + self.transmission_timeout
                    > time.time()
            ):

                timeleft = int((self.data_channel_last_received + self.transmission_timeout) - time.time())
                self.states.set("arq_seconds_until_timeout", timeleft)
                if timeleft % 10 == 0:
                    self.log.debug("Time left until channel timeout", seconds=timeleft)

                # threading.Event().wait(5)
                # print(self.data_channel_last_received + self.transmission_timeout - time.time())
                # pass
            else:
                # Clear the timeout timestamp
                self.data_channel_last_received = 0
                self.log.info(
                    "[Modem] DATA ["
                    + str(self.mycallsign, "UTF-8")
                    + "]<<T>>["
                    + str(self.dxcallsign, "UTF-8")
                    + "]"
                )
                self.event_manager.send_custom_event(
                    freedata="modem-message",
                    arq="transmission",
                    status="failed",
                    uuid=self.transmission_uuid,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                    irs=helpers.bool_to_string(self.is_IRS)
                )
                self.arq_cleanup()

    def arq_session_keep_alive_watchdog(self) -> None:
        """
        watchdog which checks if we are running into a connection timeout
        ARQ SESSION
        """
        if (
                self.states.is_arq_session
                and self.states.is_modem_busy
                and not self.arq_file_transfer
        ):
            if self.arq_session_last_received + self.arq_session_timeout > time.time():
                threading.Event().wait(0.01)
            else:
                self.log.info(
                    "[Modem] SESSION ["
                    + str(self.mycallsign, "UTF-8")
                    + "]<<T>>["
                    + str(self.dxcallsign, "UTF-8")
                    + "]"
                )
                self.event_manager.send_custom_event(
                    freedata="modem-message",
                    arq="session",
                    status="failed",
                    reason="timeout",
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )
                self.close_session()

    def heartbeat(self) -> None:
        """
        Heartbeat thread which auto pauses and resumes the heartbeat signal when in an arq session
        """
        while True:
            threading.Event().wait(0.01)
            # additional check for smoother stopping if heartbeat transmission
            while not self.arq_file_transfer:
                threading.Event().wait(0.01)
                if (
                        self.states.is_arq_session
                        and self.IS_ARQ_SESSION_MASTER
                        and self.states.arq_session_state == "connected"
                        # and not self.arq_file_transfer
                ):
                    threading.Event().wait(1)
                    self.transmit_session_heartbeat()
                    threading.Event().wait(2)

