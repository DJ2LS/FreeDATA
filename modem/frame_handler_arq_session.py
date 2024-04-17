from queue import Queue
import frame_handler
from event_manager import EventManager
from state_manager import StateManager
from modem_frametypes import FRAME_TYPE as FR
from arq_session_irs import ARQSessionIRS
from arq_session_iss import ARQSessionISS

class ARQFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):

        if not self.should_respond():
            return

        frame = self.details['frame']
        session_id = frame['session_id']
        snr = self.details["snr"]
        frequency_offset = self.details["frequency_offset"]

        if frame['frame_type_int'] == FR.ARQ_SESSION_OPEN.value:

            # Lost OPEN_ACK case .. ISS will retry opening a session
            if session_id in self.states.arq_irs_sessions:
                session = self.states.arq_irs_sessions[session_id]

            # Normal case when receiving a SESSION_OPEN for the first time
            else:
                if self.states.check_if_running_arq_session():
                    self.logger.warning("DISCARDING SESSION OPEN because of ongoing ARQ session ", frame=frame)
                    return
                session = ARQSessionIRS(self.config,
                                        self.modem,
                                        frame['origin'], 
                                        session_id,
                                        self.states)
                self.states.register_arq_irs_session(session)

        elif frame['frame_type_int'] in [
            FR.ARQ_SESSION_INFO.value,
            FR.ARQ_BURST_FRAME.value,
            FR.ARQ_STOP.value,
        ]:
            session = self.states.get_arq_irs_session(session_id)

        elif frame['frame_type_int'] in [
            FR.ARQ_SESSION_OPEN_ACK.value,
            FR.ARQ_SESSION_INFO_ACK.value,
            FR.ARQ_BURST_ACK.value,
            FR.ARQ_STOP_ACK.value
        ]:
            session = self.states.get_arq_iss_session(session_id)

        else:
            self.logger.warning("DISCARDING FRAME", frame=frame)
            return

        session.set_details(snr, frequency_offset)
        session.on_frame_received(frame)
