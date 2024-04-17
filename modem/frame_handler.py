import helpers
from event_manager import EventManager
from state_manager import StateManager
from queue import Queue
import structlog
import time, uuid
from codec2 import FREEDV_MODE
from message_system_db_manager import DatabaseManager
import maidenhead

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

    def is_frame_for_me(self):
        call_with_ssid = self.config['STATION']['mycall'] + "-" + str(self.config['STATION']['myssid'])
        ft = self.details['frame']['frame_type']
        valid = False
        # Check for callsign checksum
        if ft in ['ARQ_SESSION_OPEN', 'ARQ_SESSION_OPEN_ACK', 'PING', 'PING_ACK', 'P2P_CONNECTION_CONNECT']:
            valid, mycallsign = helpers.check_callsign(
                call_with_ssid,
                self.details["frame"]["destination_crc"],
                self.config['STATION']['ssid_list'])

        # Check for session id on IRS side
        elif ft in ['ARQ_SESSION_INFO', 'ARQ_BURST_FRAME', 'ARQ_STOP']:
            session_id = self.details['frame']['session_id']
            if session_id in self.states.arq_irs_sessions:
                valid = True

        # Check for session id on ISS side
        elif ft in ['ARQ_SESSION_INFO_ACK', 'ARQ_BURST_ACK', 'ARQ_STOP_ACK']:
            session_id = self.details['frame']['session_id']
            if session_id in self.states.arq_iss_sessions:
                valid = True

        # check for p2p connection
        elif ft in ['P2P_CONNECTION_CONNECT']:
            valid, mycallsign = helpers.check_callsign(
                call_with_ssid,
                self.details["frame"]["destination_crc"],
                self.config['STATION']['ssid_list'])

        #check for p2p connection
        elif ft in ['P2P_CONNECTION_CONNECT_ACK', 'P2P_CONNECTION_PAYLOAD', 'P2P_CONNECTION_PAYLOAD_ACK', 'P2P_CONNECTION_DISCONNECT', 'P2P_CONNECTION_DISCONNECT_ACK']:
            session_id = self.details['frame']['session_id']
            if session_id in self.states.p2p_connection_sessions:
                valid = True

        else:
            valid = False

        if not valid:
            self.logger.info(f"[Frame handler] {ft} received but not for us.")

        return valid

    def should_respond(self):
        return self.is_frame_for_me()



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

        if "AWAY_FROM_KEY" in frame["flag"]:
            activity["away_from_key"] = frame["flag"]["AWAY_FROM_KEY"]

        self.states.add_activity(activity)

    def add_to_heard_stations(self):
        frame = self.details['frame']

        if 'origin' not in frame:
            return

        dxgrid = frame.get('gridsquare', "------")
        # Initialize distance values
        distance_km = None
        distance_miles = None
        if dxgrid != "------" and frame.get('gridsquare'):
            distance_dict = maidenhead.distance_between_locators(self.config['STATION']['mygrid'], frame['gridsquare'])
            distance_km = distance_dict['kilometers']
            distance_miles = distance_dict['miles']

        helpers.add_to_heard_stations(
            frame['origin'],
            dxgrid,
            self.name,
            self.details['snr'],
            self.details['frequency_offset'],
            self.states.radio_frequency,
            self.states.heard_stations,
            distance_km=distance_km,  # Pass the kilometer distance
            distance_miles=distance_miles,  # Pass the miles distance
            away_from_key=self.details['frame']["flag"]["AWAY_FROM_KEY"]
        )
    def make_event(self):

        event = {
            "type": "frame-handler",
            "received": self.details['frame']['frame_type'],
            "timestamp": int(time.time()),
            "mycallsign": self.config['STATION']['mycall'],
            "myssid": self.config['STATION']['myssid'],
            "snr": str(self.details['snr']),
        }
        if 'origin' in self.details['frame']:
            event['dxcallsign'] = self.details['frame']['origin']

        if 'gridsquare' in self.details['frame']:
            event['gridsquare'] = self.details['frame']['gridsquare']

            distance = maidenhead.distance_between_locators(self.config['STATION']['mygrid'], self.details['frame']['gridsquare'])
            event['distance_kilometers'] = distance['kilometers']
            event['distance_miles'] = distance['miles']

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
        self.logger.info(f"[Frame Handler] Handling frame {self.details['frame']['frame_type']}")

    def handle(self, frame, snr, frequency_offset, freedv_inst, bytes_per_frame):
        self.details['frame'] = frame
        self.details['snr'] = snr
        self.details['frequency_offset'] = frequency_offset
        self.details['freedv_inst'] = freedv_inst
        self.details['bytes_per_frame'] = bytes_per_frame

        # look in database for a full callsign if only crc is present
        if 'origin' not in frame and 'origin_crc' in frame:
            self.details['frame']['origin'] = DatabaseManager(self.event_manager).get_callsign_by_checksum(frame['origin_crc'])

        self.log()
        self.add_to_heard_stations()
        self.add_to_activity_list()
        self.emit_event()
        self.follow_protocol()
