import time
import ujson as json
class STATES:
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
        self.is_beacon_running = False
        self.is_arq_state = False
        self.is_arq_session = False
        self.is_transmitting = False
        self.arq_session_state = 'disconnected'
        self.audio_dbfs = 0

    def set(self, key, value):
        setattr(self, key, value)
        updateCandence = 3
        # only process data if changed
        # but also send an update if more than a 'updateCadence' second(s) has lapsed
        # Otherwise GUI can't tell if modem is active due to lack of state messages on startup
        new_state = self.getAsJSON()
        if new_state != self.newstate or time.time() - self.last > updateCandence:
            self.statequeue.put(new_state)
            self.newstate = new_state
            self.last=time.time()

    def getAsJSON(self):
        return json.dumps({
            "freedata-message": "state-change",
            "channel_busy": self.channel_busy,
            "is_codec2_traffic": self.is_codec2_traffic,
            "is_modem_running": self.is_modem_running,
            "is_beacon_running": self.is_beacon_running,

        })