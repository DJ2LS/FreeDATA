import time
import ujson as json
class STATES:
    def __init__(self, statequeue):
        self.statequeue = statequeue
        self.newstate = None
        self.channel_busy = False
        self.channel_busy_slot = [False, False, False, False, False]
        self.is_codec2_traffic = False
        self.is_modem_running = False
        self.is_beacon_running = False
        self.is_arq_state = False
        self.is_arq_session = False
        self.arq_session_state = 'disconnected'
        self.audio_dbfs = 0
    
    def sendStateUpdate (self):
            self.statequeue.put(self.newstate)
            

    def set(self, key, value):
        setattr(self, key, value)
        # only process data if changed
        # but also send an update if more than a 'updateCadence' second(s) has lapsed
        # Otherwise GUI can't tell if modem is active due to lack of state messages on startup
        new_state = self.getAsJSON()
        if new_state != self.newstate:
            self.newstate = new_state
            self.sendStateUpdate()
            

    def getAsJSON(self):
        return json.dumps({
            "freedata-message": "state-change",
            "channel_busy": self.channel_busy,
            "is_codec2_traffic": self.is_codec2_traffic,
            "is_modem_running": self.is_modem_running,
            "is_beacon_running": self.is_beacon_running,

        })