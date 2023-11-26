import time
import ujson as json
import threading
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
        self.heard_stations = []

        self.arq_instance_table = {}
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



    def register_arq_instance_by_id(self, id, instance):
        self.arq_instance_table[id] = instance

    def get_arq_instance_by_id(self, id):
        return self.arq_instance_table.get(id)

    def delete_arq_instance_by_id(self, id):
        instances = self.arq_instance_table.pop(id, None)
        if None not in instances:
            for key in instances:
                del instances[key]
            return True
        return False

