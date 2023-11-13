
import ujson as json
class STATES:
    def __init__(self, statequeue):
        self.statequeue = statequeue

        self.channel_busy = False
        self.channel_busy_slot = [False, False, False, False, False]
        self.is_codec2_traffic = False
        self.is_modem_running = False
        self.is_beacon_running = False
        self.audio_dbfs = 0

    def set(self, key, value):
        setattr(self, key, value)
        self.statequeue.put(self.getAsJSON())

    def getAsJSON(self):
        return json.dumps({
            "freedata-message": "state-change",
            "channel_busy": self.channel_busy,
            "is_codec2_traffic": self.is_codec2_traffic,
            "is_modem_running": self.is_modem_running,
            "is_beacon_running": self.is_beacon_running,

        })