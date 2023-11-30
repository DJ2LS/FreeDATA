import json
import structlog

class EventManager:

    def __init__(self, queues):
        self.queues = queues
        self.log = structlog.get_logger('Event Manager')
        self.lastpttstate = False

    def broadcast(self, data):
        self.log.debug(f"Broadcasting event: {data}")
        for q in self.queues:
            q.put(data)

    def send_ptt_change(self, on:bool = False):
        if (on == self.lastpttstate):
            return
        self.lastpttstate= on
        self.broadcast({"ptt": bool(on)})

    def send_scatter_change(self, data):
        self.broadcast({"scatter": str(data)})

    def send_buffer_overflow(self, data):
        self.broadcast({"buffer-overflow": str(data)})

    def send_custom_event(self, **event_data):
        self.broadcast(event_data)
