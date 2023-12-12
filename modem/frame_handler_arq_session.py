from queue import Queue
import frame_handler
from event_manager import EventManager
from state_manager import StateManager
from modem_frametypes import FRAME_TYPE as FR
from arq_session_irs import ARQSessionIRS
from arq_session_iss import ARQSessionISS

class ARQFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):
        # self.details == {'frame': {'frame_type': 'BURST_01', 'frame_type_int': 1, 'n_frames_per_burst': 1, 'session_id': 31, 'data': b'Hello world!'}, 'snr': 0, 'frequency_offset': 0, 'freedv_inst': None, 'bytes_per_frame': 15}
        frame = self.details['frame']

        # ARQ session open received
        if frame['frame_type_int'] in [FR.ARQ_SESSION_OPEN_N.value, FR.ARQ_SESSION_OPEN_W.value]:
            session = ARQSessionIRS(self.config, 
                                    self.tx_frame_queue, 
                                    frame['origin'], 
                                    frame['session_id'], 
                                    frame['frame_type_int'] == FR.ARQ_SESSION_OPEN_W.value)
            self.states.register_arq_irs_session(session, frame['frame_type_int'] == FR.ARQ_SESSION_OPEN_W.value)
            session.run()

        # ARQ session open ack received
        elif frame['frame_type_int'] in [FR.ARQ_SESSION_OPEN_ACK_N.value, FR.ARQ_SESSION_OPEN_ACK_W.value]:
            iss_session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            iss_session.on_connection_ack_received(frame)

        # ARQ session data frame received
        elif frame['frame_type_int'] in [FR.BURST_01.value, FR.BURST_02.value, FR.BURST_03.value, FR.BURST_04.value, FR.BURST_05.value]:
            print("received data frame....")
            irs_session:ARQSessionIRS = self.states.get_arq_irs_session(frame['session_id'])
            irs_session.on_data_received(frame)
