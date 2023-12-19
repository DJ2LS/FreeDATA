import queue, threading
import codec2
import data_frame_factory
import structlog
from event_manager import EventManager
from modem_frametypes import FRAME_TYPE

class ARQSession():

    SPEED_LEVEL_DICT = {
        0: {
            'mode': codec2.FREEDV_MODE.datac4,
            'min_snr': -10,
            'duration_per_frame': 5.17,
        },
        1: {
            'mode': codec2.FREEDV_MODE.datac3,
            'min_snr': 0,
            'duration_per_frame': 3.19,
        },
        2: {
            'mode': codec2.FREEDV_MODE.datac1,
            'min_snr': 3,
            'duration_per_frame': 4.18,
        },
    }


    """
        helpers.set_flag(byte, 'DATA-ACK-NACK', True, FLAG_POSITIONS)
        helpers.get_flag(byte, 'DATA-ACK-NACK', FLAG_POSITIONS)    
    """
    FLAG_POSITIONS = {
        'DATA-ACK-NACK': 0,  # Bit position for DATA-ACK-NACK
    }

    def __init__(self, config: dict, modem, dxcall: str):
        self.logger = structlog.get_logger(type(self).__name__)
        self.config = config

        self.event_manager: EventManager = modem.event_manager

        self.snr = []

        self.dxcall = dxcall
        self.dx_snr = []

        self.modem = modem
        self.speed_level = 0
        self.frames_per_burst = 1

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)
        self.event_frame_received = threading.Event()

        self.id = None

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
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
        self.snr.append(snr)
        self.frequency_offset = frequency_offset

    def on_frame_received(self, frame):
        self.event_frame_received.set()
        self.log(f"Received {frame['frame_type']}")
        frame_type = frame['frame_type_int']
        if self.state in self.STATE_TRANSITION:
            if frame_type in self.STATE_TRANSITION[self.state]:
                action_name = self.STATE_TRANSITION[self.state][frame_type]
                getattr(self, action_name)(frame)
                return
        
        self.log(f"Ignoring unknow transition from state {self.state} with frame {frame['frame_type']}")
