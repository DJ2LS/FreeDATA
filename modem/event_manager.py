import json

class EventManager:

    def __init__(self, queues):
        self.queues = queues

    def broadcast(self, data):
        for q in self.queues:
            q.put(data)

    def send_ptt_change(self, on:bool = False):
        self.broadcast({"ptt": str(on)})

    def send_scatter_change(self, data):
        self.broadcast({"scatter": str(data)})

    def send_buffer_overflow(self, data):
        self.broadcast({"buffer-overflow": str(data)})

    def send_custom_event(self, **event_data):
        self.broadcast(event_data)
