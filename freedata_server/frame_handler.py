import helpers
from event_manager import EventManager
from state_manager import StateManager
import structlog
import time
from codec2 import FREEDV_MODE
from message_system_db_manager import DatabaseManager
from message_system_db_station import DatabaseManagerStations

import maidenhead

TESTMODE = False


class FrameHandler():
    """Base class for handling received frames.

        This class provides common functionality for processing received frames,
        including checking if the frame is addressed to the current station,
        adding activity to the activity list, managing heard stations, emitting
        events, and transmitting responses. Subclasses implement the
        `follow_protocol` method to handle specific frame types and protocols.
    """
    def __init__(self, name: str, config, states: StateManager, event_manager: EventManager, modem, socket_interface_manager) -> None:
        """Initializes a new FrameHandler instance.

            Args:
                name (str): The name of the frame handler.
                config (dict): The configuration dictionary.
                states (StateManager): The state manager object.
                event_manager (EventManager): The event manager object.
                modem: The modem object.
        """
        self.name = name
        self.config = config
        self.states = states
        self.event_manager = event_manager
        self.socket_interface_manager = socket_interface_manager
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
        """Checks if the received frame is addressed to this station.

        This method checks if the received frame is intended for this
        station by verifying the destination callsign CRC and SSID against
        the station's configured callsign and SSID list. It also checks for
        session IDs in the case of ARQ and P2P frames.

        Returns:
            bool: True if the frame is for this station, False otherwise.
        """
        call_with_ssid = self.config['STATION']['mycall'] + "-" + str(self.config['STATION']['myssid'])
        ft = self.details['frame']['frame_type']
        valid = False
                
        # Check for callsign checksum
        if ft in ['ARQ_SESSION_OPEN', 'ARQ_SESSION_OPEN_ACK', 'PING', 'PING_ACK']:

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
            #Need to make sure this does not affect any other features in FreeDATA.
            #This will allow the client to respond to any call sent in the "MYCALL" command

            #print("check......")
            #self.details["frame"]["mycallsign_crc"] = helpers.get_crc_24(self.details["frame"]["mycallsign"])
            #print("Jaaaa?")

            print(self.details)

            self.details["frame"]["destination_crc"] = helpers.get_crc_24(self.details["frame"]["destination"])

            print(helpers.get_crc_24(self.details["frame"]["destination"]))

            print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            if self.socket_interface_manager and self.socket_interface_manager.socket_interface_callsigns:
                print("checking callsings....")
                print(self.socket_interface_manager.socket_interface_callsigns)
                for callsign in self.socket_interface_manager.socket_interface_callsigns:
                    print("check:", callsign)
                    valid, mycallsign = helpers.check_callsign(
                        callsign,
                        self.details["frame"]["destination_crc"].hex(),
                        self.config['STATION']['ssid_list'])
                    if valid is True:
                        break
            else:
                print("no socket interface manager")
                valid, mycallsign = helpers.check_callsign(
                    call_with_ssid,
                    self.details["frame"]["destination_crc"].hex(),
                    self.config['STATION']['ssid_list'])
            print("check done .... ")


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
        """Checks if the frame handler should respond to the received frame.

        This method simply calls is_frame_for_me() to determine if a
        response is necessary. It can be overridden by subclasses to
        implement more complex response logic.

        Returns:
            bool: True if the handler should respond, False otherwise.
        """
        return self.is_frame_for_me()

    def is_origin_on_blacklist(self):
        """Checks if the origin callsign is on the blacklist.

        This method checks if the origin callsign of the received frame is
        present in the callsign blacklist defined in the configuration.
        It handles callsigns with SSIDs by removing the suffix and performs
        a case-insensitive comparison.

        Returns:
            bool: True if the origin callsign is blacklisted, False otherwise.
        """
        origin_callsign = self.details["frame"]["origin"]

        for blacklist_callsign in self.config["STATION"]["callsign_blacklist"]:
            if helpers.get_crc_24(origin_callsign).hex() == helpers.get_crc_24(blacklist_callsign).hex():
                return True

            if origin_callsign == blacklist_callsign or origin_callsign.startswith(blacklist_callsign):
                return True
        return False


    def add_to_activity_list(self):
        """Adds the received frame to the activity list.

        This method extracts relevant information from the received frame,
        such as origin, destination, gridsquare, SNR, frequency offset,
        activity type, session ID, and away-from-key status, and adds it
        as a new activity to the state manager's activity list.
        """
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

        if "flag" in frame:
            if "AWAY_FROM_KEY" in frame["flag"]:
                activity["away_from_key"] = frame["flag"]["AWAY_FROM_KEY"]

        self.states.add_activity(activity)

    def add_to_heard_stations(self):
        """Adds the received frame's origin station to the heard stations list.

        This method extracts information from the received frame, including
        callsign, gridsquare, signal strength, frequency offset, and
        away-from-key status, and adds it to the heard stations list in the
        state manager. It also calculates the distance between the current
        station and the received station if gridsquares are available.
        """
        frame = self.details['frame']

        if 'origin' not in frame:
            return

        dxgrid = frame.get('gridsquare', "------")


        # Initialize distance values
        distance_km = None
        distance_miles = None
        if dxgrid != "------":
            distance_dict = maidenhead.distance_between_locators(self.config['STATION']['mygrid'], dxgrid)
            distance_km = distance_dict['kilometers']
            distance_miles = distance_dict['miles']

        away_from_key = False
        if "flag" in self.details['frame']:
            if "AWAY_FROM_KEY" in self.details['frame']["flag"]:
                away_from_key = self.details['frame']["flag"]["AWAY_FROM_KEY"]

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
            away_from_key=away_from_key
        )
    def make_event(self):
        """Creates a frame received event dictionary.

        This method constructs a dictionary containing information about the
        received frame, including timestamps, callsigns, gridsquares, signal
        strength, and distance. This dictionary is used for emitting events
        related to frame reception.

        Returns:
            dict: A dictionary containing the event data.
        """

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
            if event['gridsquare'] != "------":
                distance = maidenhead.distance_between_locators(self.config['STATION']['mygrid'], self.details['frame']['gridsquare'])
                event['distance_kilometers'] = distance['kilometers']
                event['distance_miles'] = distance['miles']
            else:
                event['distance_kilometers'] = 0
                event['distance_miles'] = 0

        if "flag" in self.details['frame'] and "AWAY_FROM_KEY" in self.details['frame']["flag"]:
            event['away_from_key'] = self.details['frame']["flag"]["AWAY_FROM_KEY"]

        return event

    def emit_event(self):
        """Emits a frame received event.

        This method creates an event dictionary containing information about
        the received frame, such as the frame type, timestamp, callsigns,
        gridsquare, SNR, distance, and away-from-key status. It then
        broadcasts this event through the event manager.
        """
        event_data = self.make_event()
        print(event_data)
        self.event_manager.broadcast(event_data)

    def get_tx_mode(self):
        """Returns the transmission mode for acknowledgements.

        This method returns the FreeDV mode used for transmitting
        acknowledgement frames. Currently, it always returns the signalling
        mode.

        Returns:
            FREEDV_MODE: The FreeDV mode for transmissions.
        """
        return FREEDV_MODE.signalling

    def transmit(self, frame):
        """Transmits a frame using the modem.

        This method transmits the given frame using the modem. In test mode,
        it broadcasts the frame through the event manager instead of using
        the modem.

        Args:
            frame: The frame to transmit.
        """
        if not TESTMODE:
            self.modem.transmit(self.get_tx_mode(), 1, 0, frame)
        else:
            self.event_manager.broadcast(frame)

    def follow_protocol(self):
        """Handles protocol-specific actions for the received frame.

        This method is intended to be overridden by subclasses to implement
        specific protocol handling logic for different frame types. The base
        implementation does nothing.
        """
        pass

    def log(self):
        """Logs the frame type being handled."""
        self.logger.info(f"[Frame Handler] Handling frame {self.details['frame']['frame_type']}")

    def handle(self, frame, snr, frequency_offset, freedv_inst, bytes_per_frame):
        """Handles a received frame.

        This method processes the received frame, updates internal state,
        performs blacklist checks, adds the frame to activity lists and heard
        stations, emits an event, and calls the follow_protocol method for
        subclass-specific handling.

        Args:
            frame (dict): The received frame data.
            snr (float): The signal-to-noise ratio of the received frame.
            frequency_offset (float): The frequency offset of the received frame.
            freedv_inst: The FreeDV instance.
            bytes_per_frame (int): The number of bytes per frame.

        Returns:
            bool: True if the frame was processed successfully, False if it was blocked due to blacklisting.
        """

        self.details['frame'] = frame
        self.details['snr'] = snr
        self.details['frequency_offset'] = frequency_offset
        self.details['freedv_inst'] = freedv_inst
        self.details['bytes_per_frame'] = bytes_per_frame

        print(self.details)

        if 'origin' not in self.details['frame'] and 'session_id' in self.details['frame']:
            dxcall = self.states.get_dxcall_by_session_id(self.details['frame']['session_id'])
            if dxcall:
                self.details['frame']['origin'] = dxcall

        # look in database for a full callsign if only crc is present
        if 'origin' not in self.details['frame'] and 'origin_crc' in self.details['frame']:
            self.details['frame']['origin'] = DatabaseManager(self.event_manager).get_callsign_by_checksum(frame['origin_crc'])

        if "location" in self.details['frame'] and "gridsquare" in self.details['frame']['location']:
            DatabaseManagerStations(self.event_manager).update_station_location(self.details['frame']['origin'], frame['gridsquare'])


        if 'origin' in self.details['frame']:
            # try to find station info in database
            try:
                station = DatabaseManagerStations(self.event_manager).get_station(self.details['frame']['origin'])
                if station and station["location"] and "gridsquare" in station["location"]:
                    dxgrid = station["location"]["gridsquare"]
                else:
                    dxgrid = "------"

                # overwrite gridsquare only if not provided by frame
                if "gridsquare" not in self.details['frame']:
                    self.details['frame']['gridsquare'] = dxgrid

            except Exception as e:
                self.logger.info(f"[Frame Handler] Error getting gridsquare from callsign info: {e}")

        # check if callsign is blacklisted
        if self.config["STATION"]["enable_callsign_blacklist"]:
            if self.is_origin_on_blacklist():
                self.logger.info(f"[Frame Handler] Callsign blocked: {self.details['frame']['origin']}")
                return False

        self.log()
        self.add_to_heard_stations()
        self.add_to_activity_list()
        self.emit_event()
        self.follow_protocol()
        return True
