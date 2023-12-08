from queue import Queue
import frame_handler
from event_manager import EventManager
from state_manager import StateManager
from modem_frametypes import FRAME_TYPE as FR
from arq_session_irs import ARQSessionIRS
from arq_session_iss import ARQSessionISS

class ARQFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):
        frame = self.details['frame']

        # ARQ session open received
        if frame['frame_type_int'] in [FR.ARQ_SESSION_OPEN_N.value, FR.ARQ_SESSION_OPEN_W.value]:
            session = ARQSessionIRS(self.config, 
                                    self.tx_frame_queue, 
                                    frame['origin'], frame['session_id'])
            self.states.register_arq_irs_session(session)
            session.run()

        # ARQ session open ack received
        if frame['frame_type_int'] in [FR.ARQ_SESSION_OPEN_ACK_N.value, FR.ARQ_SESSION_OPEN_ACK_W.value]:
            iss_session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            iss_session.on_connection_ack_received(frame)