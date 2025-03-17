import datetime
import threading
import data_frame_factory
import structlog
from event_manager import EventManager
from modem_frametypes import FRAME_TYPE
import time
from arq_data_type_handler import ARQDataTypeHandler
from codec2 import FREEDV_MODE_USED_SLOTS, FREEDV_MODE
import stats
class ARQSession:
    """Manages an ARQ (Automatic Repeat reQuest) session.

    This class handles the transmission and reception of data using the ARQ protocol,
    managing session state, statistics, and data handling.
    """
    SPEED_LEVEL_DICT = {
        0: {
            'mode': FREEDV_MODE.datac4,
            'min_snr': -10,
            'duration_per_frame': 5.17,
            'bandwidth': 250,
            'slots': FREEDV_MODE_USED_SLOTS.datac4,
        },
        1: {
            'mode': FREEDV_MODE.data_ofdm_500,
            'min_snr': 0,
            'duration_per_frame': 3.19,
            'bandwidth': 500,
            'slots': FREEDV_MODE_USED_SLOTS.data_ofdm_500,
        },
        2: {
            'mode': FREEDV_MODE.datac1,
            'min_snr': 3,
            'duration_per_frame': 4.18,
            'bandwidth': 1700,
            'slots': FREEDV_MODE_USED_SLOTS.datac1,
        },
        3: {
            'mode': FREEDV_MODE.data_ofdm_2438,
            'min_snr': 8.5,
            'duration_per_frame': 5.5,
            'bandwidth': 2438,
            'slots': FREEDV_MODE_USED_SLOTS.data_ofdm_2438,
        },
        # 4: {
        #    'mode': FREEDV_MODE.qam16c2,
        #    'min_snr': 11,
        #    'duration_per_frame': 2.8,
        #    'bandwidth': 2438,
        #    'slots': FREEDV_MODE_USED_SLOTS.qam16c2,
        # },
    }

    def __init__(self, config: dict, modem, dxcall: str, state_manager):
        """Initializes a new ARQ session.

        This method sets up the ARQ session with the provided configuration,
        modem, DX call sign, and state manager. It initializes various
        session parameters and data structures.

        Args:
            config (dict): The configuration dictionary.
            modem: The modem object.
            dxcall (str): The DX call sign.
            state_manager: The state manager object.
        """
        self.logger = structlog.get_logger(type(self).__name__)
        self.config = config

        self.event_manager: EventManager = modem.event_manager
        #self.states = freedata_server.states
        self.states = state_manager
        self.states.setARQ(True)

        self.is_IRS = False # state for easy check "is IRS" or is "ISS"

        self.protocol_version = 1

        self.snr = []

        self.dxcall = dxcall
        self.dx_snr = []

        self.modem = modem
        self.speed_level = 0
        self.previous_speed_level = 0

        self.frames_per_burst = 1

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)
        self.event_frame_received = threading.Event()

        self.arq_data_type_handler = ARQDataTypeHandler(self.event_manager, self.states)
        self.id = None
        self.session_started = time.time()
        self.session_ended = 0
        self.session_max_age = 500

        # this timestamp is updated by "set_state", everytime we have a state change.
        # we will use the schedule manager, for checking, how old is the state change for deciding, how we continue with the message
        self.last_state_change_timestamp = time.time()

        self.statistics = stats.stats(self.config, self.event_manager, self.states)

        # histogram lists for storing statistics
        self.snr_histogram = []
        self.bpm_histogram = []
        self.bps_histogram = []
        self.time_histogram = []

    def log(self, message, isWarning=False):
        """Logs a message with session context.

        Logs a message, including the class name, session ID, and current state,
        using the appropriate log level (warning or info).

        Args:
            message: The message to be logged.
            isWarning: A boolean indicating whether the message should be logged as a warning.
        """
        msg = f"[{type(self).__name__}][id={self.id}][state={self.state}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def get_mode_by_speed_level(self, speed_level):
        """Returns the FreeDV mode for the given speed level.

        This method retrieves the FreeDV mode associated with a specific speed level
        from the SPEED_LEVEL_DICT.

        Args:
            speed_level (int): The speed level.

        Returns:
            modem_frametypes.FREEDV_MODE: The FreeDV mode corresponding to the speed level.
        """
        return self.SPEED_LEVEL_DICT[speed_level]["mode"]

    def transmit_frame(self, frame: bytearray, mode='auto'):
        """Transmits a given frame using the modem.

        This method transmits the provided frame using the configured modem.
        If the mode is set to 'auto', it determines the appropriate FreeDV mode
        based on the current speed level.

        Args:
            frame (bytearray): The frame to be transmitted.
            mode (str, optional): The FreeDV mode to use for transmission. Defaults to 'auto'.
        """
        self.log("Transmitting frame")
        if mode in ['auto']:
            mode = self.get_mode_by_speed_level(self.speed_level)

        self.modem.transmit(mode, 1, 1, frame)

    def set_state(self, state):
        """Sets the state of the ARQ session.

        This method updates the session state and logs the state change.
        It also updates the timestamp of the last state change.

        Args:
            state: The new state of the ARQ session.
        """
        self.last_state_change_timestamp = time.time()
        if self.state == state:
            self.log(f"{type(self).__name__} state {self.state.name} unchanged.")
        else:
            self.log(f"{type(self).__name__} state change from {self.state.name} to {state.name} at {self.last_state_change_timestamp}")
        self.state = state

    def get_data_payload_size(self):
        """Returns the available data payload size for the current speed level.

        This method calculates the available data payload size for ARQ burst frames
        based on the current speed level and FreeDV mode.

        Returns:
            int: The available data payload size in bytes.
        """
        return self.frame_factory.get_available_data_payload_for_mode(
            FRAME_TYPE.ARQ_BURST_FRAME,
            self.SPEED_LEVEL_DICT[self.speed_level]["mode"]
            )

    def set_details(self, snr, frequency_offset):
        """Sets the SNR and frequency offset for the ARQ session.

        This method updates the signal-to-noise ratio (SNR) and frequency offset
        values for the current session.

        Args:
            snr: The signal-to-noise ratio.
            frequency_offset: The frequency offset.
        """
        self.snr = snr
        self.frequency_offset = frequency_offset

    def on_frame_received(self, frame):
        """Handles received frames based on the current session state.

        This method processes incoming frames, triggering state transitions and
        data handling based on the frame type and current session state.
        It logs received frame types and ignores unknown state transitions.

        Args:
            frame: The received frame.
        """
        self.event_frame_received.set()
        self.log(f"Received {frame['frame_type']}")
        frame_type = frame['frame_type_int']
        if self.state in self.STATE_TRANSITION and frame_type in self.STATE_TRANSITION[self.state]:
            action_name = self.STATE_TRANSITION[self.state][frame_type]
            received_data, type_byte = getattr(self, action_name)(frame)

            if isinstance(received_data, bytearray) and isinstance(type_byte, int):
                self.arq_data_type_handler.dispatch(type_byte, received_data,
                                                    self.update_histograms(len(received_data), len(received_data)))
            return

        self.log(f"Ignoring unknown transition from state {self.state.name} with frame {frame['frame_type']}")

    def is_session_outdated(self):
        """Checks if the session is outdated.

        This method checks if the session has ended and if the end time is
        older than the session_max_age. It returns True if the session is
        outdated, False otherwise.

        Returns:
            bool: True if the session is outdated, False otherwise.
        """
        session_alivetime = time.time() - self.session_max_age
        return self.session_ended < session_alivetime and self.state.name in [
            'FAILED',
            'ENDED',
            'ABORTED',
        ]

    def calculate_session_duration(self):
        """Calculates the duration of the ARQ session.

        This method calculates the duration of the session, taking into account
        whether the session has ended or is still ongoing.

        Returns:
            float: The duration of the session in seconds.
        """
        if self.session_ended == 0:
            return time.time() - self.session_started

        return self.session_ended - self.session_started

    def calculate_session_statistics(self, confirmed_bytes, total_bytes):
        """Calculates session statistics.

        This method calculates various statistics for the ARQ session, including
        duration, bytes per minute, bits per second, and histograms for time,
        SNR, BPM, and BPS.

        Args:
            confirmed_bytes: The number of confirmed bytes transmitted.
            total_bytes: The total number of bytes transmitted.

        Returns:
            dict: A dictionary containing the calculated session statistics.
        """
        duration = self.calculate_session_duration()
        # total_bytes = self.total_length
        # self.total_length
        duration_in_minutes = duration / 60  # Convert duration from seconds to minutes

        # Calculate bytes per minute
        if duration_in_minutes > 0:
            bytes_per_minute = int(confirmed_bytes / duration_in_minutes)
        else:
            bytes_per_minute = 0

        # Calculate bits per second
        bits_per_second = int((confirmed_bytes * 8) / duration)


        # Convert histograms lists to dictionaries
        time_histogram_dict = dict(enumerate(self.time_histogram))
        snr_histogram_dict = dict(enumerate(self.snr_histogram))
        bpm_histogram_dict = dict(enumerate(self.bpm_histogram))
        bps_histogram_dict = dict(enumerate(self.bps_histogram))

        return {
            'total_bytes': total_bytes,
            'duration': duration,
            'bytes_per_minute': bytes_per_minute,
            'bits_per_second': bits_per_second,
            'time_histogram': time_histogram_dict,
            'snr_histogram': snr_histogram_dict,
            'bpm_histogram': bpm_histogram_dict,
            'bps_histogram': bps_histogram_dict,
        }

    def update_histograms(self, confirmed_bytes, total_bytes):
        """Updates session histograms with the latest statistics.

        This method calculates and updates the histograms for SNR, bytes per
        minute (BPM), bits per second (BPS), and time, using the provided
        confirmed and total bytes. It limits the histogram size to the last
        20 entries.

        Args:
            confirmed_bytes: The number of confirmed bytes transmitted.
            total_bytes: The total number of bytes transmitted.

        Returns:
            dict: A dictionary containing the calculated session statistics.
        """
        stats = self.calculate_session_statistics(confirmed_bytes, total_bytes)
        self.snr_histogram.append(self.snr)
        self.bpm_histogram.append(stats['bytes_per_minute'])
        self.bps_histogram.append(stats['bits_per_second'])
        self.time_histogram.append(datetime.datetime.now().isoformat())

        # Limit the size of each histogram to the last 20 entries
        self.snr_histogram = self.snr_histogram[-20:]
        self.bpm_histogram = self.bpm_histogram[-20:]
        self.bps_histogram = self.bps_histogram[-20:]
        self.time_histogram = self.time_histogram[-20:]

        return stats

    def check_channel_busy(self, channel_busy_slot, mode_slot):
        """Checks if the channel is busy based on channel busy slots and mode slots.

        This method iterates through the channel_busy_slot and mode_slot lists.
        It returns False if a channel is both busy and the mode is active,
        indicating the channel is available. Otherwise, it returns True.

        Args:
            channel_busy_slot: A list of booleans representing channel busy status.
            mode_slot: A list of booleans representing mode activity status.

        Returns:
            bool: True if the channel is available, False otherwise.
        """
        for busy, mode in zip(channel_busy_slot, mode_slot):
            if busy and mode:
                return False
        return True

    def get_appropriate_speed_level(self, snr, maximum_bandwidth=None):
        """
        Determines the appropriate speed level based on the SNR, channel busy slot, and maximum bandwidth.

        Parameters:
        - snr (float): The signal-to-noise ratio.
        - channel_busy_slot (list of bool): The busy condition of the channels.
        - maximum_bandwidth (float, optional): The maximum bandwidth. If None, uses the default from the configuration.

        Returns:
        - int: The appropriate speed level.
        """
        # Use default maximum bandwidth from configuration if not provided
        if maximum_bandwidth is None:
            maximum_bandwidth = self.config['MODEM']['maximum_bandwidth']

        # Adjust maximum_bandwidth if set to 0 (use maximum available bandwidth from speed levels)
        if maximum_bandwidth == 0:
            maximum_bandwidth = max(details['bandwidth'] for details in self.SPEED_LEVEL_DICT.values())

        # Iterate through speed levels in reverse order to find the highest appropriate one
        for level in sorted(self.SPEED_LEVEL_DICT.keys(), reverse=True):
            details = self.SPEED_LEVEL_DICT[level]
            mode_slots = details['slots'].value
            if (snr >= details['min_snr'] and
                details['bandwidth'] <= maximum_bandwidth and
                self.check_channel_busy(self.states.channel_busy_slot, mode_slots)):
                return level

        # Return the lowest level if no higher level is found
        return min(self.SPEED_LEVEL_DICT.keys())
    
    def reset_session(self):
        """Resets the ARQ session to its initial state.

        This method clears all session-related data, including received bytes,
        histograms, type byte, total length, CRC values, received data,
        maximum bandwidth, and the abort flag.
        """
        self.received_bytes = 0
        self.snr_histogram = []
        self.bpm_histogram = []
        self.bps_histogram = []
        self.time_histogram = []
        self.type_byte = None
        self.total_length = 0
        self.total_crc = ''
        self.received_data = None
        self.received_bytes = 0
        self.received_crc = None
        self.maximum_bandwidth = 0
        self.abort = False