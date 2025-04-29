from queue import Queue
from event_manager import EventManager
from state_manager import StateManager
from schedule_manager import ScheduleManager
from config import CONFIG
from service_manager import SM as ServiceManager
from message_system_db_manager import DatabaseManager
from message_system_db_attachments import DatabaseManagerAttachments
from websocket_manager import wsm as WebsocketManager
import audio
import constants
from fastapi import Request, WebSocket
class AppContext:
    def __init__(self, config_file: str):
        self.config_manager   = CONFIG(self, config_file)
        self.constants = constants
        self.p2p_data_queue   = Queue()
        self.state_queue      = Queue()
        self.modem_events     = Queue()
        self.modem_fft        = Queue()
        self.modem_service    = Queue()
        self.event_manager    = EventManager([self.modem_events])
        self.state_manager    = StateManager(self.state_queue)
        self.schedule_manager = ScheduleManager(self)
        self.service_manager  = ServiceManager(self)
        self.websocket_manager = WebsocketManager(self)

        self.socket_interface_manager = None # Socket interface instance, We start it as we need it
        self.rf_modem = None # Modem instnace, we start it as we need it
        self.message_system_db_manager = DatabaseManager(self.event_manager)
        self.message_system_db_attachments = DatabaseManagerAttachments(self.event_manager)

    def startup(self):

        # initially read config
        self.config_manager.read()

        self.websocket_manager.startWorkerThreads(self)

        # start modem service
        self.modem_service.put("start")

        # DB setup
        db = DatabaseManager(self.event_manager)
        db.check_database_version()
        db.initialize_default_values()
        db.database_repair_and_cleanup()
        DatabaseManagerAttachments(self.event_manager).clean_orphaned_attachments()


        # Audio cleanup on shutdown
        self._audio = audio

    def shutdown(self):
        try:
            for s in self.state_manager.arq_irs_sessions.values():
                s.transmission_aborted()
            for s in self.state_manager.arq_iss_sessions.values():
                s.abort_transmission(send_stop=False)
                s.transmission_aborted()
        except Exception:
            pass
        self.websocket_manager.shutdown()
        self.schedule_manager.stop()
        self.service_manager.shutdown()
        self._audio.terminate()

# Dependency provider for FastAPI (HTTP & WebSocket)
def get_ctx(request: Request = None, websocket: WebSocket = None) -> AppContext:
    """
    Provide the application context for HTTP requests or WebSocket connections.

    FastAPI will pass either a Request or WebSocket instance.

    Returns:
        AppContext: The application context stored in state.
    """
    conn = request or websocket
    return conn.app.state.ctx
