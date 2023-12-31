import helpers
from event_manager import EventManager
from state_manager import StateManager
from queue import Queue
import structlog
import time, uuid
from codec2 import FREEDV_MODE

TESTMODE = False

class FrameHandler():

    def __init__(self, name: str, config, states: StateManager, event_manager: EventManager, 
                 modem) -> None:
        
        self.name = name
        self.config = config
        self.states = states
        self.event_manager = event_manager
        self.modem = modem
        self.logger = structlog.get_logger("Frame Handler")

        self.details = {
            'frame' : None, 
            'snr' : 0, 
            'frequency_offset': 0,
            'freedv_inst': None, 
            'bytes_per_frame': 0
        }



    def add_to_activity_list(self):
        frame = self.details['frame']

        activity = {
            "direction": "received",
            "snr": self.details['snr'],
            "frequency_offset": self.details['frequency_offset'],
            "activity_type": frame["frame_type"]
        }
        if "origin" in frame:
            activity["origin"] = frame["origin"]

        if "destination" in frame:
            activity["destination"] = frame["destination"]

        if "gridsquare" in frame:
            activity["gridsquare"] = frame["gridsquare"]

        if "session_id" in frame:
            activity["session_id"] = frame["session_id"]

        self.states.add_activity(activity)


    def add_to_heard_stations(self):
        frame = self.details['frame']

        if 'origin' not in frame:
            return

        dxgrid = frame['gridsquare'] if 'gridsquare' in frame else "------"
        helpers.add_to_heard_stations(
            frame['origin'],
            dxgrid,
            self.name,
            self.details['snr'],
            self.details['frequency_offset'],
            self.states.radio_frequency,
            self.states.heard_stations,
        )

    def make_event(self):
        event = {
            "freedata": "modem-message",
            "received": self.details['frame']['frame_type'],
            "uuid": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "mycallsign": self.config['STATION']['mycall'],
            "snr": str(self.details['snr']),
        }        
        if 'origin' in self.details['frame']:
            event['dxcallsign'] = self.details['frame']['origin']
        return event

    def emit_event(self):
        event_data = self.make_event()
        self.event_manager.broadcast(event_data)

    def get_tx_mode(self):
        return FREEDV_MODE.signalling

    def transmit(self, frame):
        if not TESTMODE:
            self.modem.transmit(self.get_tx_mode(), 1, 0, frame)
        else:
            self.event_manager.broadcast(frame)

    def follow_protocol(self):
        pass

    def log(self):
        return
        self.logger.info(f"[Frame Handler] Handling frame {self.details['frame']['frame_type']}")

    def handle(self, frame, snr, frequency_offset, freedv_inst, bytes_per_frame):
        self.details['frame'] = frame
        self.details['snr'] = snr
        self.details['frequency_offset'] = frequency_offset
        self.details['freedv_inst'] = freedv_inst
        self.details['bytes_per_frame'] = bytes_per_frame

        self.log()
        self.add_to_heard_stations()
        self.add_to_activity_list()
        self.emit_event()
        self.follow_protocol()
