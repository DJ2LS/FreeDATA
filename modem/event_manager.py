import base64
import json
import structlog

class EventManager:

    def __init__(self, queues):
        self.queues = queues
        self.logger = structlog.get_logger('Event Manager')
        self.lastpttstate = False

    def broadcast(self, data):
        for q in self.queues:
            self.logger.debug(f"Event: ", ev=data)
            if q.qsize() > 10:
                q.queue.clear()
            q.put(data)

    def send_ptt_change(self, on:bool = False):
        if (on == self.lastpttstate):
            return
        self.lastpttstate= on
        self.broadcast({"ptt": bool(on)})

    def send_scatter_change(self, data):
        self.broadcast({"scatter": json.dumps(data)})

    def send_buffer_overflow(self, data):
        self.broadcast({"buffer-overflow": str(data)})

    def send_custom_event(self, **event_data):
        self.broadcast(event_data)

    def send_arq_session_new(self, outbound: bool, session_id, dxcall, total_bytes, state):
        direction = 'outbound' if outbound else 'inbound'
        event = {
                "type": "arq",
                f"arq-transfer-{direction}": {
                'session_id': session_id,
                'dxcall': dxcall,
                'total_bytes': total_bytes,
                'state': state,
            }
        }
        self.broadcast(event)

    def send_arq_session_progress(self, outbound: bool, session_id, dxcall, received_bytes, total_bytes, state, statistics=None):
        if statistics is None:
            statistics = {}

        direction = 'outbound' if outbound else 'inbound'
        event = {
                "type": "arq",
                f"arq-transfer-{direction}": {
                'session_id': session_id,
                'dxcall': dxcall,
                'received_bytes': received_bytes,
                'total_bytes': total_bytes,
                'state': state,
                'statistics': statistics,
            }
        }
        self.broadcast(event)

    def send_arq_session_finished(self, outbound: bool, session_id, dxcall, success: bool, state: bool, data=False, statistics=None):
        if statistics is None:
            statistics = {}
        if data:
            data = base64.b64encode(data).decode("UTF-8")
        direction = 'outbound' if outbound else 'inbound'
        event = {
                "type" : "arq",
                f"arq-transfer-{direction}": {
                'session_id': session_id,
                'dxcall': dxcall,
                'statistics': statistics,
                'success': bool(success),
                'state': state,
                'data': data
            }
        }
        self.broadcast(event)

    def modem_started(self):
        event = {"modem": "started"}
        self.broadcast(event)

    def modem_restarted(self):
        event = {"modem": "restarted"}
        self.broadcast(event)

    def modem_stopped(self):
        event = {"modem": "stopped"}
        self.broadcast(event)

    def modem_failed(self):
        event = {"modem": "failed"}
        self.broadcast(event)

    def freedata_message_db_change(self):
        self.broadcast({"message-db": "changed"})