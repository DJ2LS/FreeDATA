from queue import Queue
import frame_handler
from event_manager import EventManager
from state_manager import StateManager
from modem_frametypes import FRAME_TYPE as FR
from arq_session_irs import ARQSessionIRS
from arq_session_iss import ARQSessionISS
from arq_session_irs import IRS_State


class ARQFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):

        if not self.should_respond():
            return

        frame = self.details['frame']
        session_id = frame['session_id']
        snr = self.details["snr"]
        frequency_offset = self.details["frequency_offset"]

        if frame['frame_type_int'] == FR.ARQ_SESSION_OPEN.value:
            print("Received ARQ_SESSION_OPEN frame")
            print(f"Session ID: {session_id}")

            # Handle cases where the session_id is already present in arq_irs_sessions
            if session_id in self.states.arq_irs_sessions:
                print(f"ARQ session already in memory: {session_id}")
                session = self.states.arq_irs_sessions[session_id]
                current_state = session.state
                print(f"ARQ session state: {current_state}")


                # Lost OPEN_ACK case .. ISS will retry opening a session
                if current_state in [IRS_State.NEW, IRS_State.OPEN_ACK_SENT]:
                    print("Lost OPEN_ACK case: ISS will retry opening a session.")
                # Case where a transmission has failed, we want to continue the transmission
                elif current_state in [IRS_State.FAILED, IRS_State.ABORTED]:
                    print("Transmission failed: Will continue the transmission.")
                    # TODO Lets consider adding an additional state here
                    session.state = IRS_State.NEW

                # Case where we just want to retransmit an already transmitted message
                elif current_state == IRS_State.ENDED:
                    print("Retransmitting an already transmitted message.")
                    session.reset_session()
                    session.state = IRS_State.NEW

            # Normal case when receiving a SESSION_OPEN for the first time
            else:
                print("First-time reception of SESSION_OPEN frame.")
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
            print("Received ARQ frame of type: INFO, BURST, or STOP.")
            session = self.states.get_arq_irs_session(session_id)

        elif frame['frame_type_int'] in [
            FR.ARQ_SESSION_OPEN_ACK.value,
            FR.ARQ_SESSION_INFO_ACK.value,
            FR.ARQ_BURST_ACK.value,
            FR.ARQ_STOP_ACK.value
        ]:
            print("Received ARQ ACK frame of type: OPEN_ACK, INFO_ACK, BURST_ACK, or STOP_ACK.")
            session = self.states.get_arq_iss_session(session_id)

        else:
            self.logger.warning("DISCARDING FRAME", frame=frame)
            return

        session.set_details(snr, frequency_offset)
        session.on_frame_received(frame)
