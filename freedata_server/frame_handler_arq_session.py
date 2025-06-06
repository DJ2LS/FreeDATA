from queue import Queue
import frame_handler
from event_manager import EventManager
from state_manager import StateManager
from modem_frametypes import FRAME_TYPE as FR
from arq_session_irs import ARQSessionIRS
from arq_session_iss import ARQSessionISS
from arq_session_irs import IRS_State


class ARQFrameHandler(frame_handler.FrameHandler):
    """Handles ARQ frames and manages ARQ sessions.

    This class processes incoming ARQ frames, manages ARQ sessions for both
    ISS (Information Sending Station) and IRS (Information Receiving Station),
    and dispatches frames to the appropriate session based on their type
    and session ID.
    """

    def follow_protocol(self):
        """Processes the received ARQ frame based on its type.

        This method handles different ARQ frame types, including session
        open, information, burst data, stop, and various acknowledgements.
        It manages session creation, retrieval, and updates based on the
        frame type and session ID.
        """

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
            if session_id in self.ctx.state_manager.arq_irs_sessions:
                print(f"ARQ session already in memory: {session_id}")
                session = self.ctx.state_manager.arq_irs_sessions[session_id]
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
                if self.ctx.state_manager.check_if_running_arq_session():
                    self.logger.warning("DISCARDING SESSION OPEN because of ongoing ARQ session ", frame=frame)
                    return
                session = ARQSessionIRS(self.ctx,frame['origin'],session_id)
                self.ctx.state_manager.register_arq_irs_session(session)

        elif frame['frame_type_int'] in [
            FR.ARQ_SESSION_INFO.value,
            FR.ARQ_BURST_FRAME.value,
            FR.ARQ_STOP.value,
        ]:
            print("Received ARQ frame of type: INFO, BURST, or STOP.")
            session = self.ctx.state_manager.get_arq_irs_session(session_id)

        elif frame['frame_type_int'] in [
            FR.ARQ_SESSION_OPEN_ACK.value,
            FR.ARQ_SESSION_INFO_ACK.value,
            FR.ARQ_BURST_ACK.value,
            FR.ARQ_STOP_ACK.value
        ]:
            print("Received ARQ ACK frame of type: OPEN_ACK, INFO_ACK, BURST_ACK, or STOP_ACK.")
            session = self.ctx.state_manager.get_arq_iss_session(session_id)

        else:
            self.logger.warning("DISCARDING FRAME", frame=frame)
            return

        session.set_details(snr, frequency_offset)
        session.on_frame_received(frame)
