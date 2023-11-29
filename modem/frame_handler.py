import helpers
from event_manager import EventManager
from state_manager import StateManager
from queue import Queue
import structlog

class FrameHandler():

    def __init__(self, name: str, states: StateManager, event_manager: EventManager, 
                 tx_frame_queue: Queue,
                 arq_sessions: list) -> None:
        
        self.name = name
        self.states = states
        self.event_manager = event_manager
        self.tx_trame_queue = tx_frame_queue
        self.arq_sessions = arq_sessions
        self.logger = structlog.get_logger("Frame Handler")

    def add_to_heard_stations(self):
        pass

    def make_event(self, frame):
        return {
            "freedata": "generic frame handler",
            "frame": frame,
        }

    def emit_event(self, frame):
        event_data = self.make_event(frame)
        self.event_manager.broadcast(event_data)

    def make_modem_queue_item(self, mode, repeat, repeat_delay, frame):
        return {
            'mode': self.get_tx_mode(),
            'repeat': 1,
            'repeat_delay': 0,
            'frame': frame,
        }

    def transmit(self, frame):
        tx_queue_item = self.make_modem_queue_item(self.get_tx_mode(), 1, 0, frame)
        self.tx_frame_queue.put(tx_queue_item)

    def follow_protocol(self):
        pass

    def log(self, frame):
        self.logger.info(f"[Frame Handler] Handling frame {frame}")
        pass

    def handle(self, frame, snr, freq_offset, freedv_inst, bytes_per_frame):
        self.log(frame)
        self.add_to_heard_stations()
        self.emit_event(frame)
        self.follow_protocol()
