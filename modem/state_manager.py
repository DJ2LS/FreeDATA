

class STATES:
    def __init__(self, statequeue):
        self.statequeue = statequeue
        self.testvalue = "Hello World!"


        self.channel_busy = False
        self.channel_busy_slot = [False, False, False, False, False]
        self.is_codec2_traffic = False

    def set(self, key, value):
        setattr(self, key, value)
        self.statequeue.put(self.getAsJSON())

    def getAsJSON(self):
        return {
            "freedata-message": "state-change",
            "channel_busy": self.channel_busy,
            "is_codec2_traffic": self.is_codec2_traffic
        }