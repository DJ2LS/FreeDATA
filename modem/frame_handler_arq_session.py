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
        snr = self.details["snr"]
        frequency_offset = self.details["frequency_offset"]

        if frame['frame_type_int'] == FR.ARQ_SESSION_OPEN.value:
            session = ARQSessionIRS(self.config, 
                                    self.tx_frame_queue, 
                                    frame['origin'], 
                                    frame['session_id'])
            self.states.register_arq_irs_session(session)
            session.run()

        elif frame['frame_type_int'] == FR.ARQ_SESSION_OPEN_ACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.on_open_ack_received(frame)

        elif frame['frame_type_int'] == FR.ARQ_SESSION_INFO_ACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.on_info_ack_received(frame)

        elif frame['frame_type_int'] == FR.BURST_FRAME.value:
            session:ARQSessionIRS = self.states.get_arq_irs_session(frame['session_id'])
            session.on_data_received(frame)

        elif frame['frame_type_int'] == FR.BURST_ACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.on_burst_ack_received(frame)

        elif frame['frame_type_int'] == FR.BURST_NACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.on_burst_nack_received(frame)
