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
        snr = self.details["snr"]
        frequency_offset = self.details["frequency_offset"]

        if frame['frame_type_int'] == FR.ARQ_SESSION_OPEN.value:
            # Lost OPEN_ACK case .. ISS will retry opening a session
            if frame['session_id'] in self.states.arq_irs_sessions:
                session = self.states.arq_irs_sessions[frame['session_id']]
                if session.state in [ARQSessionIRS.STATE_CONN_REQ_RECEIVED, ARQSessionIRS.STATE_WAITING_INFO]:
                    session.set_details(snr, frequency_offset)
                else:
                    self.logger.warning(f"IRS Session conflict for session {session.id}")
            # Normal case when receiving a SESSION_OPEN for the first time
            else:
                session = ARQSessionIRS(self.config, 
                                        self.tx_frame_queue, 
                                        frame['origin'], 
                                        frame['session_id'])
                self.states.register_arq_irs_session(session)
                session.set_details(snr, frequency_offset)
                session.run()

        elif frame['frame_type_int'] == FR.ARQ_SESSION_OPEN_ACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.set_details(snr, frequency_offset)
            session.on_open_ack_received(frame)

        elif frame['frame_type_int'] == FR.ARQ_SESSION_INFO.value:
            session:ARQSessionIRS = self.states.get_arq_irs_session(frame['session_id'])
            session.set_details(snr, frequency_offset)
            session.on_info_received(frame)

        elif frame['frame_type_int'] == FR.ARQ_SESSION_INFO_ACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.set_details(snr, frequency_offset)
            session.on_info_ack_received(frame)

        elif frame['frame_type_int'] == FR.ARQ_BURST_FRAME.value:
            session:ARQSessionIRS = self.states.get_arq_irs_session(frame['session_id'])
            session.set_details(snr, frequency_offset)
            session.on_data_received(frame)

        elif frame['frame_type_int'] == FR.ARQ_BURST_ACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.set_details(snr, frequency_offset)
            session.on_burst_ack_received(frame)

        elif frame['frame_type_int'] == FR.ARQ_DATA_ACK_NACK.value:
            session:ARQSessionISS = self.states.get_arq_iss_session(frame['session_id'])
            session.set_details(snr, frequency_offset)
            session.on_data_ack_nack_received(frame)
        else:
            self.logger.warning("DISCARDING FRAME", frame=frame)
