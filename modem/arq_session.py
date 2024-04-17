import datetime
import threading
import codec2
import data_frame_factory
import structlog
from event_manager import EventManager
from modem_frametypes import FRAME_TYPE
import time
from arq_data_type_handler import ARQDataTypeHandler


class ARQSession:

    SPEED_LEVEL_DICT = {
        0: {
            'mode': codec2.FREEDV_MODE.datac4,
            'min_snr': -10,
            'duration_per_frame': 5.17,
            'bandwidth': 250,
        },
        1: {
            'mode': codec2.FREEDV_MODE.datac3,
            'min_snr': 0,
            'duration_per_frame': 3.19,
            'bandwidth': 563,
        },
        2: {
            'mode': codec2.FREEDV_MODE.datac1,
            'min_snr': 3,
            'duration_per_frame': 4.18,
            'bandwidth': 1700,
        },
        3: {
            'mode': codec2.FREEDV_MODE.data_ofdm_2438,
            'min_snr': 8,
            'duration_per_frame': 6.5,
            'bandwidth': 2438,
        },
        4: {
            'mode': codec2.FREEDV_MODE.qam16c2,
            'min_snr': 11,
            'duration_per_frame': 2.8,
            'bandwidth': 2438,
        },
    }

    def __init__(self, config: dict, modem, dxcall: str, state_manager):
        self.logger = structlog.get_logger(type(self).__name__)
        self.config = config

        self.event_manager: EventManager = modem.event_manager
        #self.states = modem.states
        self.states = state_manager
        self.states.setARQ(True)

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

        # histogram lists for storing statistics
        self.snr_histogram = []
        self.bpm_histogram = []
        self.time_histogram = []

    def log(self, message, isWarning=False):
        msg = f"[{type(self).__name__}][id={self.id}][state={self.state}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def get_mode_by_speed_level(self, speed_level):
        return self.SPEED_LEVEL_DICT[speed_level]["mode"]

    def transmit_frame(self, frame: bytearray, mode='auto'):
        self.log("Transmitting frame")
        if mode in ['auto']:
            mode = self.get_mode_by_speed_level(self.speed_level)

        self.modem.transmit(mode, 1, 1, frame)

    def set_state(self, state):
        if self.state == state:
            self.log(f"{type(self).__name__} state {self.state.name} unchanged.")
        else:
            self.log(f"{type(self).__name__} state change from {self.state.name} to {state.name}")
        self.state = state

    def get_data_payload_size(self):
        return self.frame_factory.get_available_data_payload_for_mode(
            FRAME_TYPE.ARQ_BURST_FRAME,
            self.SPEED_LEVEL_DICT[self.speed_level]["mode"]
            )

    def set_details(self, snr, frequency_offset):
        self.snr = snr
        self.frequency_offset = frequency_offset

    def on_frame_received(self, frame):
        self.event_frame_received.set()
        self.log(f"Received {frame['frame_type']}")
        frame_type = frame['frame_type_int']
        if self.state in self.STATE_TRANSITION and frame_type in self.STATE_TRANSITION[self.state]:
            action_name = self.STATE_TRANSITION[self.state][frame_type]
            received_data, type_byte = getattr(self, action_name)(frame)
            if isinstance(received_data, bytearray) and isinstance(type_byte, int):
                self.arq_data_type_handler.dispatch(type_byte, received_data, self.update_histograms(len(received_data), len(received_data)))
            return
        
        self.log(f"Ignoring unknown transition from state {self.state.name} with frame {frame['frame_type']}")

    def is_session_outdated(self):
        session_alivetime = time.time() - self.session_max_age
        return self.session_ended < session_alivetime and self.state.name in [
            'FAILED',
            'ENDED',
            'ABORTED',
        ]

    def calculate_session_duration(self):
        if self.session_ended == 0:
            return time.time() - self.session_started

        return self.session_ended - self.session_started

    def calculate_session_statistics(self, confirmed_bytes, total_bytes):
        duration = self.calculate_session_duration()
        # total_bytes = self.total_length
        # self.total_length
        duration_in_minutes = duration / 60  # Convert duration from seconds to minutes

        # Calculate bytes per minute
        if duration_in_minutes > 0:
            bytes_per_minute = int(confirmed_bytes / duration_in_minutes)
        else:
            bytes_per_minute = 0

        # Convert histograms lists to dictionaries
        time_histogram_dict = dict(enumerate(self.time_histogram))
        snr_histogram_dict = dict(enumerate(self.snr_histogram))
        bpm_histogram_dict = dict(enumerate(self.bpm_histogram))

        return {
            'total_bytes': total_bytes,
            'duration': duration,
            'bytes_per_minute': bytes_per_minute,
            'time_histogram': time_histogram_dict,
            'snr_histogram': snr_histogram_dict,
            'bpm_histogram': bpm_histogram_dict,
        }

    def update_histograms(self, confirmed_bytes, total_bytes):

        stats = self.calculate_session_statistics(confirmed_bytes, total_bytes)
        self.snr_histogram.append(self.snr)
        self.bpm_histogram.append(stats['bytes_per_minute'])
        self.time_histogram.append(datetime.datetime.now().isoformat())

        # Limit the size of each histogram to the last 20 entries
        self.snr_histogram = self.snr_histogram[-20:]
        self.bpm_histogram = self.bpm_histogram[-20:]
        self.time_histogram = self.time_histogram[-20:]

        return stats

    def get_appropriate_speed_level(self, snr, maximum_bandwidth=None):
        if maximum_bandwidth is None:
            maximum_bandwidth = self.config['MODEM']['maximum_bandwidth']

        # Adjust maximum_bandwidth based on special conditions or invalid configurations
        if maximum_bandwidth == 0:
            # Use the maximum available bandwidth from the speed level dictionary
            maximum_bandwidth = max(details['bandwidth'] for details in self.SPEED_LEVEL_DICT.values())

        # Initialize appropriate_speed_level to the lowest level that meets the minimum criteria
        appropriate_speed_level = min(self.SPEED_LEVEL_DICT.keys())

        for level, details in self.SPEED_LEVEL_DICT.items():
            if snr >= details['min_snr'] and details['bandwidth'] <= maximum_bandwidth and level > appropriate_speed_level:
                appropriate_speed_level = level

        return appropriate_speed_level
