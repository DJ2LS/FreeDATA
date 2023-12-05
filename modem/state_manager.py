import time
import ujson as json
import threading
import numpy as np
class StateManager:
    def __init__(self, statequeue):

        # state related settings
        self.statequeue = statequeue
        self.newstate = None
        self.last = time.time()

        # modem related states
        # not every state is needed to publish, yet
        # TODO can we reduce them?
        self.channel_busy = False
        self.channel_busy_slot = [False, False, False, False, False]
        self.is_codec2_traffic = False
        self.is_modem_running = False
        self.is_modem_busy = False
        self.is_beacon_running = False
        self.is_arq_state = False
        self.is_arq_session = False

        # If true, any wait() call is blocking
        self.transmitting_event = threading.Event()
        self.setTransmitting(False)
        
        self.audio_dbfs = 0
        self.dxcallsign: bytes = b"ZZ9YY-0"
        self.dxgrid: bytes = b"------"

        self.heard_stations = []  # TODO remove it... heard stations list == deprecated
        self.activities_list = {}

        self.arq_iss_sessions = {}
        self.arq_irs_sessions = {}
        
        self.arq_session_state = 'disconnected'
        self.arq_speed_level = 0
        self.arq_total_bytes = 0
        self.arq_bits_per_second = 0
        self.arq_bytes_per_minute = 0
        self.arq_transmission_percent = 0
        self.arq_compression_factor = 0
        self.arq_speed_list = []
        self.arq_seconds_until_timeout = 0

        self.mesh_routing_table = []

        self.radio_frequency = 0
        self.radio_mode = None
        self.radio_bandwidth = 0
        self.radio_rf_power = 0
        self.radio_strength = 0
        # Set rig control status regardless or rig control method
        self.radio_status = False

    def sendState (self):
        currentState = self.get_state_event(False)
        self.statequeue.put(currentState)
        return currentState

    def sendStateUpdate (self):
        self.statequeue.put(self.newstate)

    def set(self, key, value):
        setattr(self, key, value)
        #print(f"State ==> Setting {key} to value {value}")
        # only process data if changed
        new_state = self.get_state_event(True)
        if new_state != self.newstate:
            self.newstate = new_state
            self.sendStateUpdate()

    def set_channel_slot_busy(self, array):
        for i in range(0,len(array),1):
            if not array[i] == self.channel_busy_slot[i]:
                self.channel_busy_slot = array
                self.newstate = self.get_state_event(True)
                self.sendStateUpdate()
                continue
    
    def get_state_event(self, isChangedState):
        msgtype = "state-change"
        if (not isChangedState):
            msgtype = "state"

        return {
            "freedata-message": msgtype,
            "channel_busy": self.channel_busy,
            "is_codec2_traffic": self.is_codec2_traffic,
            "is_modem_running": self.is_modem_running,
            "is_beacon_running": self.is_beacon_running,
            "radio_status": self.radio_status,
            "radio_frequency": self.radio_frequency,
            "radio_mode": self.radio_mode,
            "channel_busy_slot": self.channel_busy_slot,
            "audio_dbfs": self.audio_dbfs,
            "activities": self.activities_list,
        }
    
    # .wait() blocks until the event is set
    def isTransmitting(self):
        return not self.transmitting_event.is_set()
    
    # .wait() blocks until the event is set
    def setTransmitting(self, transmitting: bool):
        if transmitting:
            self.transmitting_event.clear()
        else:
            self.transmitting_event.set()

    def waitForTransmission(self):
        self.transmitting_event.wait()

    def register_arq_iss_session(self, session):
        if session.id in self.arq_iss_sessions:
            raise RuntimeError(f"ARQ ISS Session '{session.id}' already exists!")
        self.arq_iss_sessions[session.id] = session

    def register_arq_irs_session(self, session):
        if session.id in self.arq_irs_sessions:
            raise RuntimeError(f"ARQ IRS Session '{session.id}' already exists!")
        self.arq_irs_sessions[session.id] = session

    def get_arq_iss_session(self, id):
        if id not in self.arq_iss_sessions:
            raise RuntimeError(f"ARQ ISS Session '{id}' not found!")
        return self.arq_iss_sessions[id]

    def get_arq_irs_session(self, id):
        if id not in self.arq_irs_sessions:
            raise RuntimeError(f"ARQ IRS Session '{id}' not found!")
        return self.arq_irs_sessions[id]

    def remove_arq_iss_session(self, id):
        if id not in self.arq_iss_sessions:
            raise RuntimeError(f"ARQ ISS Session '{id}' not found!")
        del self.arq_iss_sessions[id]

    def remove_arq_irs_session(self, id):
        if id not in self.arq_irs_sessions:
            raise RuntimeError(f"ARQ ISS Session '{id}' not found!")
        del self.arq_irs_sessions[id]

    def add_activity(self, activity_data):
        # Generate a random 8-byte string as hex
        activity_id = np.random.bytes(8).hex()

        # if timestamp not provided, add it here
        if 'timestamp' not in activity_data:
            activity_data['timestamp'] = int(time.time())

        # if frequency not provided, add it here
        if 'frequency' not in activity_data:
            activity_data['frequency'] = self.radio_frequency

        self.activities_list[activity_id] = activity_data
        self.sendStateUpdate()
