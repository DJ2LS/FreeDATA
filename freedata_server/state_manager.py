import time
import threading
import numpy as np
class StateManager:
    """Manages and updates the state of the FreeDATA server.

    This class stores and manages various state variables related to the
    FreeDATA server, including modem status, channel activity, ARQ sessions,
    radio parameters, and P2P connections. It provides methods to update
    and retrieve state information, as well as manage events and
    synchronization.
    """
    def __init__(self, statequeue):

        # state related settings
        self.statequeue = statequeue
        self.newstate = None
        self.newradio = None
        self.last = time.time()

        # freedata_server related states
        # not every state is needed to publish, yet
        # TODO can we reduce them?
        self.channel_busy_slot = [False, False, False, False, False]
        self.channel_busy_event = threading.Event()
        self.channel_busy_condition_traffic = threading.Event()
        self.channel_busy_condition_codec2 = threading.Event()

        self.is_modem_running = False

        self.is_modem_busy = threading.Event()
        self.setARQ(False)

        self.is_beacon_running = False
        self.is_away_from_key = False

        # If true, any wait() call is blocking
        self.transmitting_event = threading.Event()
        self.setTransmitting(False)
        
        self.audio_dbfs = 0
        self.dxcallsign: bytes = b"ZZ9YY-0"
        self.dxgrid: bytes = b"------"

        self.heard_stations = []
        self.activities_list = {}

        self.arq_iss_sessions = {}
        self.arq_irs_sessions = {}

        self.p2p_connection_sessions = {}

        #self.mesh_routing_table = []

        self.radio_frequency = 0
        self.radio_mode = None
        self.radio_bandwidth = 0
        self.radio_rf_level = 0
        self.s_meter_strength = 0
        self.radio_tuner = False
        self.radio_swr = 0
        # Set rig control status regardless or rig control method
        self.radio_status = False

    def sendState(self):
        """Sends the current state to the state queue.

        This method retrieves the current state using get_state_event() and
        puts it into the state queue for processing and distribution.

        Returns:
            dict: The current state.
        """
        currentState = self.get_state_event(False)
        self.statequeue.put(currentState)
        return currentState

    def sendStateUpdate(self, state):
        """Sends a state update to the state queue.

        This method puts the given state update into the state queue for
        processing and distribution.

        Args:
            state (dict): The state update to send.
        """
        self.statequeue.put(state)

    def set(self, key, value):
        """Sets a state variable and sends an update if the state changes.

        This method sets the specified state variable to the given value.
        If the new state is different from the current state, it generates
        a state update event and sends it to the state queue.

        Args:
            key (str): The name of the state variable.
            value: The new value for the state variable.
        """
        setattr(self, key, value)
        #print(f"State ==> Setting {key} to value {value}")
        # only process data if changed
        new_state = self.get_state_event(True)
        if new_state != self.newstate:
            self.newstate = new_state
            self.sendStateUpdate(new_state)

    def set_radio(self, key, value):
        """Sets a radio parameter and sends an update if the value changes.

        This method sets the specified radio parameter to the given value.
        If the new value is different from the current value, it generates
        a radio update event and sends it to the state queue.

        Args:
            key (str): The name of the radio parameter.
            value: The new value for the radio parameter.
        """
        setattr(self, key, value)
        #print(f"State ==> Setting {key} to value {value}")
        # only process data if changed
        new_radio = self.get_radio_event(True)
        if new_radio != self.newradio:
            self.newradio = new_radio
            self.sendStateUpdate(new_radio)

    def set_channel_slot_busy(self, array):
        """Sets the channel busy status for each slot.

        This method updates the channel busy status for each slot based on
        the provided array. If any slot's status changes, it generates a
        state update event and sends it to the state queue.

        Args:
            array (list): A list of booleans representing the busy status of each slot.
        """
        for i in range(0,len(array),1):
            if not array[i] == self.channel_busy_slot[i]:
                self.channel_busy_slot = array
                self.newstate = self.get_state_event(True)
                self.sendStateUpdate(self.newstate)
                continue
    
    def get_state_event(self, isChangedState):
        """Generates a state event dictionary.

        This method creates a dictionary containing the current state
        information, including modem and beacon status, channel activity,
        radio status, and audio levels. The type of event ('state' or
        'state-change') is determined by the isChangedState flag.

        Args:
            isChangedState (bool): True if the event represents a state change,
                False if it's a full state update.

        Returns:
            dict: A dictionary containing the state information.
        """
        msgtype = "state-change"
        if (not isChangedState):
            msgtype = "state"

        return {
            "type": msgtype,
            "is_modem_running": self.is_modem_running,
            "is_beacon_running": self.is_beacon_running,
            "is_away_from_key": self.is_away_from_key,
            "radio_status": self.radio_status,
            "channel_busy_slot": self.channel_busy_slot,
            "is_codec2_traffic": self.is_receiving_codec2_signal(),
            "audio_dbfs": self.audio_dbfs,
            "activities": self.activities_list,
            "is_modem_busy" : self.getARQ()
        }

    def get_radio_event(self, isChangedState):
        """Generates a radio event dictionary.

        This method creates a dictionary containing the current radio state
        information, including frequency, mode, RF level, S-meter strength,
        SWR, and tuner status. The type of event ('radio' or 'radio-change')
        is determined by the isChangedState flag.

        Args:
            isChangedState (bool): True if this is a radio change event,
                False for a full radio state update.

        Returns:
            dict: A dictionary containing the radio state information.
        """
        msgtype = "radio-change"
        if (not isChangedState):
            msgtype = "radio"

        return {
            "type": msgtype,
            "radio_status": self.radio_status,
            "radio_frequency": self.radio_frequency,
            "radio_rf_level": self.radio_rf_level,
            "radio_mode": self.radio_mode,
            "s_meter_strength": self.s_meter_strength,
            "radio_swr" : self.radio_swr,
            "radio_tuner": self.radio_tuner,
        }
    
    # .wait() blocks until the event is set
    def isTransmitting(self):
        """Checks if the server is currently transmitting.

        This method returns True if the transmitting_event is not set,
        indicating that a transmission is in progress. Otherwise, it
        returns False.

        Returns:
            bool: True if transmitting, False otherwise.
        """
        return not self.transmitting_event.is_set()
    
    # .wait() blocks until the event is set
    def setTransmitting(self, transmitting: bool):
        """Sets the transmitting status of the server.

        This method controls the transmitting_event, which is used for
        synchronization and blocking other operations during transmissions.
        If transmitting is True, the event is cleared (set to non-signaled
        state), causing any threads waiting on it to block. If transmitting
        is False, the event is set (signaled state), allowing waiting
        threads to proceed.

        Args:
            transmitting (bool): True if the server is transmitting, False otherwise.
        """
        if transmitting:
            self.transmitting_event.clear()
        else:
            self.transmitting_event.set()

    def setARQ(self, busy):
        """Sets the ARQ status.

        This method sets the is_modem_busy event based on the provided
        busy flag. If busy is True, the event is cleared, indicating that
        the modem is busy with ARQ. If busy is False, the event is set,
        indicating that the modem is available.

        Args:
            busy (bool): True if ARQ is busy, False otherwise.
        """
        if busy:
            self.is_modem_busy.clear()
        else:
            self.is_modem_busy.set()

    def getARQ(self):
        """Gets the ARQ status.

        This method returns True if the is_modem_busy event is not set,
        indicating that ARQ is currently not busy. Otherwise, it returns
        False.

        Returns:
            bool: True if ARQ is not busy, False otherwise.
        """
        return not self.is_modem_busy.is_set()

    def waitForTransmission(self):
        """Waits for any ongoing transmissions to complete.

        This method blocks the calling thread until the transmitting_event
        is set, indicating that the server is no longer transmitting.
        """
        self.transmitting_event.wait()

    def waitForChannelBusy(self):
        """Waits for the channel busy event.

        This method waits for the channel_busy_event to be set, with a
        timeout of 2 seconds. This is used to pause operations when the
        channel is detected as busy.
        """
        self.channel_busy_event.wait(2)

    def register_arq_iss_session(self, session):
        """Registers an ARQ ISS session.

        This method registers an ARQ Information Sending Station (ISS) session
        by storing it in the arq_iss_sessions dictionary. It returns True
        if the session is successfully registered, False if a session with
        the same ID already exists.

        Args:
            session (ARQSessionISS): The ARQ ISS session to register.

        Returns:
            bool: True if the session was registered, False otherwise.
        """
        if session.id in self.arq_iss_sessions:
            return False
        self.arq_iss_sessions[session.id] = session
        return True

    def register_arq_irs_session(self, session):
        """Registers an ARQ IRS session.

        This method registers an ARQ Information Receiving Station (IRS)
        session, storing it in the arq_irs_sessions dictionary. It
        returns True if the session is registered successfully, or False
        if a session with the same ID already exists.

        Args:
            session (ARQSessionIRS): The ARQ IRS session to register.

        Returns:
            bool: True if the session was registered, False otherwise.
        """
        if session.id in self.arq_irs_sessions:
            return False
        self.arq_irs_sessions[session.id] = session
        return True

    def check_if_running_arq_session(self, irs=False):
        """Checks if there is a running ARQ session.

        This method iterates through either the ISS or IRS ARQ sessions,
        depending on the 'irs' flag. It cleans up outdated sessions and
        checks if any remaining sessions are not in a final state (ENDED,
        ABORTED, or FAILED).

        Args:
            irs (bool, optional): If True, checks IRS sessions; otherwise,
                checks ISS sessions. Defaults to False (ISS sessions).

        Returns:
            bool: True if there is a running ARQ session, False otherwise.
        """
        sessions = self.arq_irs_sessions if irs else self.arq_iss_sessions

        for session_id in sessions:
            # do a session cleanup of outdated sessions before
            if sessions[session_id].is_session_outdated():
                print(f"session cleanup.....{session_id}")
                if irs:
                    self.remove_arq_irs_session(session_id)
                else:
                    self.remove_arq_iss_session(session_id)

            # check again if session id exists in session because of cleanup
            if session_id in sessions and sessions[session_id].state.name not in ['ENDED', 'ABORTED', 'FAILED']:
                print(f"[State Manager] running session...[{session_id}]")
                return True
        return False

    def get_arq_iss_session(self, id):
        """Retrieves an ARQ ISS session by ID.

        This method returns the ARQ Information Sending Station (ISS) session
        associated with the given ID. If no session with the given ID is
        found, it returns None.

        Args:
            id: The ID of the ARQ ISS session.

        Returns:
            ARQSessionISS or None: The ARQSessionISS object if found, None otherwise.
        """
        if id not in self.arq_iss_sessions:
            #raise RuntimeError(f"ARQ ISS Session '{id}' not found!")
            # DJ2LS: WIP We need to find a better way of handling this
            pass
        return self.arq_iss_sessions[id]

    def get_arq_irs_session(self, id):
        """Retrieves an ARQ IRS session by ID.

        This method returns the ARQ Information Receiving Station (IRS) session
        associated with the given ID. It returns None if no session with the
        given ID is found.

        Args:
            id: The ID of the ARQ IRS session.

        Returns:
            ARQSessionIRS or None: The ARQSessionIRS object if found, None otherwise.
        """
        if id not in self.arq_irs_sessions:
            #raise RuntimeError(f"ARQ IRS Session '{id}' not found!")
            # DJ2LS: WIP We need to find a better way of handling this
            pass
        return self.arq_irs_sessions[id]

    def remove_arq_iss_session(self, id):
        """Removes an ARQ ISS session.

        This method removes the ARQ Information Sending Station (ISS) session
        associated with the given ID from the arq_iss_sessions dictionary.

        Args:
            id: The ID of the ARQ ISS session to remove.
        """
        if id in self.arq_iss_sessions:
            del self.arq_iss_sessions[id]

    def remove_arq_irs_session(self, id):
        """Removes an ARQ IRS session.

        This method removes the ARQ Information Receiving Station (IRS) session
        associated with the given ID from the arq_irs_sessions dictionary.

        Args:
            id: The ID of the ARQ IRS session to remove.
        """
        if id in self.arq_irs_sessions:
            del self.arq_irs_sessions[id]

    def stop_transmission(self):
        """Stops any ongoing ARQ transmissions.

        This method iterates through all active ARQ Information Sending Station (ISS)
        and Information Receiving Station (IRS) sessions and aborts their transmissions.
        ISS sessions are removed after being stopped, while IRS sessions are retained
        to allow for potential resumption.
        """
        # Stop and remove IRS sessions
        for session_id in list(self.arq_irs_sessions.keys()):
            session = self.arq_irs_sessions[session_id]
            session.transmission_aborted()
            # For now, we don't remove IRS session because of resuming transmissions. 
            #self.remove_arq_irs_session(session_id)

        # Stop and remove ISS sessions
        for session_id in list(self.arq_iss_sessions.keys()):
            session = self.arq_iss_sessions[session_id]
            session.abort_transmission(send_stop=False)
            session.transmission_aborted()
            self.remove_arq_iss_session(session_id)

    def add_activity(self, activity_data):
        """Adds a new activity to the activities list.

        This method generates a unique ID for the activity, adds a timestamp
        and frequency if not provided, and stores the activity data in the
        activities list. It then triggers a state update.

        Args:
            activity_data (dict): A dictionary containing the activity data.
        """
        # Generate a random 8-byte string as hex
        activity_id = np.random.bytes(8).hex()

        # if timestamp not provided, add it here
        if 'timestamp' not in activity_data:
            activity_data['timestamp'] = int(time.time())

        # if frequency not provided, add it here
        if 'frequency' not in activity_data:
            activity_data['frequency'] = self.radio_frequency
        self.activities_list[activity_id] = activity_data
        self.sendStateUpdate(self.newstate)

    def calculate_channel_busy_state(self):
        """Calculates and sets the overall channel busy state.

        This method determines the channel busy state based on the status
        of channel_busy_condition_traffic and
        channel_busy_condition_codec2. If both events are set (not busy),
        it sets the channel_busy_event, indicating the channel is available.
        Otherwise, it resets the channel_busy_event.
        """
        if self.channel_busy_condition_traffic.is_set() and self.channel_busy_condition_codec2.is_set():
            self.channel_busy_event.set()
        else:
            self.channel_busy_event = threading.Event()

    def set_channel_busy_condition_traffic(self, busy):
        """Sets the channel busy condition based on data traffic.

        This method sets or clears the channel_busy_condition_traffic event
        based on the provided busy flag. If busy is False, the event is set,
        indicating no traffic. If busy is True, the event is cleared,
        indicating traffic. It then recalculates the overall channel busy
        state.

        Args:
            busy (bool): True if there is data traffic, False otherwise.
        """
        if not busy:
            self.channel_busy_condition_traffic.set()
        else:
            self.channel_busy_condition_traffic = threading.Event()
        self.calculate_channel_busy_state()

    def set_channel_busy_condition_codec2(self, traffic):
        """Sets the channel busy condition based on Codec2 traffic.

        This method sets or clears the channel_busy_condition_codec2 event
        based on the provided traffic flag. If traffic is False, the event
        is set, indicating no Codec2 traffic. If traffic is True, the event
        is cleared, indicating ongoing Codec2 traffic. It then recalculates
        the overall channel busy state.

        Args:
            traffic (bool): True if there is Codec2 traffic, False otherwise.
        """
        if not traffic:
            self.channel_busy_condition_codec2.set()
        else:
            self.channel_busy_condition_codec2 = threading.Event()
        self.calculate_channel_busy_state()

    def is_receiving_codec2_signal(self):
        """Checks if the server is receiving a Codec2 signal.

        This method returns True if the channel_busy_condition_codec2 event
        is not set, indicating that a Codec2 signal is being received.
        Otherwise, it returns False.

        Returns:
            bool: True if a Codec2 signal is being received, False otherwise.
        """
        return not self.channel_busy_condition_codec2.is_set()

    def get_radio_status(self):
        """Returns the current radio status.

        This method returns a dictionary containing the current status
        information of the radio, including its status, frequency, mode,
        RF level, S-meter strength, SWR, and tuner status.

        Returns:
            dict: A dictionary containing the radio status information.
        """
        return {
            "radio_status": self.radio_status,
            "radio_frequency": self.radio_frequency,
            "radio_mode": self.radio_mode,
            "radio_rf_level": self.radio_rf_level,
            "s_meter_strength": self.s_meter_strength,
            "radio_swr": self.radio_swr,
            "radio_tuner": self.radio_tuner,
        }

    def register_p2p_connection_session(self, session):
        """Registers a P2P connection session.

        This method registers a peer-to-peer (P2P) connection session by
        storing it in the p2p_connection_sessions dictionary. It returns
        True if the session is successfully registered, or False if a
        session with the same ID already exists.

        Args:
            session (P2PConnection): The P2P connection session object.

        Returns:
            bool: True if the session was registered, False otherwise.
        """
        if session.session_id in self.p2p_connection_sessions:
            print("session already registered...")
            return False
        self.p2p_connection_sessions[session.session_id] = session
        return True

    def get_p2p_connection_session(self, id):
        if id not in self.p2p_connection_sessions:
            pass
        return self.p2p_connection_sessions[id]

    def get_dxcall_by_session_id(self, session_id):
        """
        Retrieves the dxcall associated with a given session ID by checking both ISS and IRS sessions.

        Args:
            session_id (str): The ID of the session.

        Returns:
            str: The dxcall associated with the session ID, or None if not found.
        """
        try:
            # Check ISS sessions
            if session_id in self.arq_iss_sessions:
                return self.arq_iss_sessions[session_id].dxcall

            # Check IRS sessions
            if session_id in self.arq_irs_sessions:
                return self.arq_irs_sessions[session_id].dxcall
#Part of the code to solve P2P connections with the ability to respond to SSIDs other than the one set on the modem.
#I will circle back around and check that this is really the best way to handle this edge case...
            if session_id in self.p2p_connection_sessions:
                return self.p2p_connection_sessions[session_id].destination

            # If not found in either session dictionary
            print(f"Session ID {session_id} not found in ISS or IRS sessions")
            return None
        except KeyError:
            print(f"Error retrieving session ID {session_id}")
            return None
