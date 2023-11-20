import json

class EventManager:

    def __init__(self, queues):
        self.queues = queues

    def broadcast(self, data):
        for q in self.queues:
            q.put(data)

    def send_ptt_change(self, on:bool = False):
        jsondata = {"ptt": str(on)}
        data_out = json.dumps(jsondata)
        self.broadcast(data_out)

    def send_scatter_change(self, data):
        jsondata = {"scatter": str(data)}
        data_out = json.dumps(jsondata)
        self.broadcast(data_out)

    def send_buffer_overflow(self, data):
        jsondata = {"buffer-overflow": str(data)}
        data_out = json.dumps(jsondata)
        self.broadcast(data_out)

    def send_custom_event(self, **jsondata):
        data_out = json.dumps(jsondata)
        self.broadcast(data_out)
