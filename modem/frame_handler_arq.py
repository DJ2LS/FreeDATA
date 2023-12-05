from queue import Queue
import frame_handler
from event_manager import EventManager
from state_manager import StateManager
from modem_frametypes import FRAME_TYPE as FR
from arq_session_irs import ARQSessionIRS

class ARQFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):
        frame = self.details['frame']

        # ARQ session open received
        if frame['frame_type_int'] in [FR.ARQ_DC_OPEN_N.value, FR.ARQ_DC_OPEN_W.value]:
            session = ARQSessionIRS(self.config, 
                                    self.tx_frame_queue, 
                                    frame['origin'], frame['session_id'])
            self.states.register_arq_irs_session(session)
            session.run()
