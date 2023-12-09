import threading
import data_frame_factory
import queue
import arq_session

class ARQSessionIRS(arq_session.ARQSession):

    STATE_CONN_REQ_RECEIVED = 0
    STATE_WAITING_DATA = 1
    STATE_FAILED = 2
    STATE_ENDED = 10

    RETRIES_CONNECT = 3
    RETRIES_TRANSFER = 3

    TIMEOUT_DATA = 6

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str, session_id: int):
        super().__init__(config, tx_frame_queue, dxcall)

        self.id = session_id

        self.received_data = b''

        self.state = self.STATE_CONN_REQ_RECEIVED

        self.event_data_received = threading.Event()
        
        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

    def generate_id(self):
        pass

    def log(self, message):
        pass

    def set_state(self, state):
        self.log(f"ARQ Session IRS {self.id} state {self.state}")
        self.state = state

    def set_modem_decode_modes(self, modes):
        pass

    def runner(self):
        isWideband = True
        speed = 1
        version = 1

        ack_frame = self.frame_factory.build_arq_session_connect_ack(isWideband, self.id, speed, version)
        self.transmit_frame(ack_frame)

        self.set_modem_decode_modes(None)
        self.state = self.STATE_WAITING_DATA
        while self.state == self.STATE_WAITING_DATA:
            if not self.event_data_received.wait(self.TIMEOUT_DATA):
                self.log("Timeout waiting for data")
                self.state = self.STATE_FAILED
                return

        self.log("Finished ARQ IRS session")

    def run(self):
        self.thread = threading.Thread(target=self.runner, name=f"ARQ IRS Session {self.id}", daemon=True)
        self.thread.start()


    def on_data_received(self, data_frame):
        if self.state != self.STATE_WAITING_DATA:
            raise RuntimeError(f"ARQ Session: Received data while in state {self.state}, expected {self.STATE_WAITING_DATA}")

        self.received_data = data_frame["data"]
        self.event_data_received.set()


    def on_transfer_ack_received(self, ack):
        self.event_transfer_ack_received.set()
        self.speed_level = ack['speed_level']

    def on_transfer_nack_received(self, nack):
        self.speed_level = nack['speed_level']

    def on_disconnect_received(self):
        self.abort()

    def abort(self):
        self.state = self.STATE_DISCONNECTED
        self.event_connection_ack_received.set()
        self.event_connection_ack_received.clear()
        self.event_transfer_feedback.set()
        self.event_transfer_feedback.clear()
        self.received_data = b''
