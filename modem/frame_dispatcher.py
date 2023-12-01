"""
FRAME DISPATCHER - We are dispatching the received frames to the needed functions


"""
import threading
import helpers
import structlog
from modem_frametypes import FRAME_TYPE as FR_TYPE
import event_manager
from queues import DATA_QUEUE_RECEIVED, DATA_QUEUE_TRANSMIT, MODEM_TRANSMIT_QUEUE
from data_frame_factory import DataFrameFactory

from data_handler_broadcasts import BROADCAST
from data_handler_data_broadcasts import DATABROADCAST
from data_handler_ping import PING

from protocol_arq_iss import ISS
from protocol_arq_irs import IRS
from protocol_arq import ARQ
from protocol_arq_session import SESSION

from frame_handler import FrameHandler
from frame_handler_ping import PingFrameHandler
from frame_handler_cq import CQFrameHandler

class DISPATCHER():

    FRAME_HANDLER = {
        FR_TYPE.ARQ_DC_OPEN_ACK_N.value: {"class": FrameHandler, "name": "ARQ OPEN ACK (Narrow)"},
        FR_TYPE.ARQ_DC_OPEN_ACK_W.value: {"class": FrameHandler, "name": "ARQ OPEN ACK (Wide)"},
        FR_TYPE.ARQ_DC_OPEN_N.value: {"class": FrameHandler, "name": "ARQ Data Channel Open (Narrow)"},
        FR_TYPE.ARQ_DC_OPEN_W.value: {"class": FrameHandler, "name": "ARQ Data Channel Open (Wide)"},
        FR_TYPE.ARQ_SESSION_CLOSE.value: {"class": FrameHandler, "name": "ARQ CLOSE SESSION"},
        FR_TYPE.ARQ_SESSION_HB.value: {"class": FrameHandler, "name": "ARQ HEARTBEAT"},
        FR_TYPE.ARQ_SESSION_OPEN.value: {"class": FrameHandler, "name": "ARQ OPEN SESSION"},
        FR_TYPE.ARQ_STOP.value: {"class": FrameHandler, "name": "ARQ STOP TX"},
        FR_TYPE.BEACON.value: {"class": FrameHandler, "name": "BEACON"},
        FR_TYPE.BURST_ACK.value: {"class": FrameHandler, "name":  "BURST ACK"},
        FR_TYPE.BURST_NACK.value: {"class": FrameHandler, "name":  "BURST NACK"},
        FR_TYPE.CQ.value: {"class": CQFrameHandler, "name":  "CQ"},
        FR_TYPE.FR_ACK.value: {"class": FrameHandler, "name":  "FRAME ACK"},
        FR_TYPE.FR_NACK.value: {"class": FrameHandler, "name":  "FRAME NACK"},
        FR_TYPE.FR_REPEAT.value: {"class": FrameHandler, "name":  "REPEAT REQUEST"},
        FR_TYPE.PING_ACK.value: {"class": FrameHandler, "name":  "PING ACK"},
        FR_TYPE.PING.value: {"class": PingFrameHandler, "name":  "PING"},
        FR_TYPE.QRV.value: {"class": FrameHandler, "name":  "QRV"},
        FR_TYPE.IS_WRITING.value: {"class": FrameHandler, "name": "IS_WRITING"},
        FR_TYPE.FEC.value: {"class": FrameHandler, "name":  "FEC"},
        FR_TYPE.FEC_WAKEUP.value: {"class": FrameHandler, "name":  "FEC WAKEUP"},
    }

    def __init__(self, config, event_queue, states, data_q_rx):
        self.log = structlog.get_logger("frame_dispatcher")

        self.log.info("loading frame dispatcher.....\n")
        self.config = config
        self.event_queue = event_queue
        self.states = states

        self._initialize_handlers(config, event_queue, states)
        self._initialize_dispatchers()

        self.data_queue_transmit = DATA_QUEUE_TRANSMIT
        self.data_queue_received = data_q_rx

        self.arq_sessions = []

    def _initialize_handlers(self, config, event_queue, states):
        """Initializes various data handlers."""

        self.frame_factory = DataFrameFactory(config)

        self.broadcasts = BROADCAST(config, event_queue, states)
        self.data_broadcasts = DATABROADCAST(config, event_queue, states)
        self.ping = PING(config, event_queue, states)

        self.arq = ARQ(config, event_queue, states)
        self.arq_irs = IRS(config, event_queue, states)
        self.arq_iss = ISS(config, event_queue, states)
        self.arq_session = SESSION(config, event_queue, states)


        self.event_manager = event_manager.EventManager([event_queue])

    def _initialize_dispatchers(self):
        """Initializes dispatchers for handling different frame types."""
        # Dictionary of functions and log messages used in process_data
        # instead of a long series of if-elif-else statements.
        self.rx_dispatcher = {
            FR_TYPE.ARQ_DC_OPEN_ACK_N.value: (
                self.arq_iss.arq_received_channel_is_open,
                "ARQ OPEN ACK (Narrow)",
            ),
            FR_TYPE.ARQ_DC_OPEN_ACK_W.value: (
                self.arq_iss.arq_received_channel_is_open,
                "ARQ OPEN ACK (Wide)",
            ),
            FR_TYPE.ARQ_DC_OPEN_N.value: (
                self.initialize_arq_transmission_irs,
                "ARQ Data Channel Open (Narrow)",
            ),
            FR_TYPE.ARQ_DC_OPEN_W.value: (
                self.initialize_arq_transmission_irs,
                "ARQ Data Channel Open (Wide)",
            ),
            FR_TYPE.ARQ_SESSION_CLOSE.value: (
                self.arq_session.received_session_close,
                "ARQ CLOSE SESSION",
            ),
            FR_TYPE.ARQ_SESSION_HB.value: (
                self.arq_session.received_session_heartbeat,
                "ARQ HEARTBEAT",
            ),
            FR_TYPE.ARQ_SESSION_OPEN.value: (
                self.arq_session.received_session_opener,
                "ARQ OPEN SESSION",
            ),
            FR_TYPE.ARQ_STOP.value: (self.arq.received_stop_transmission, "ARQ STOP TX"),
            FR_TYPE.BEACON.value: (self.broadcasts.received_beacon, "BEACON"),
            FR_TYPE.BURST_ACK.value: (self.arq_iss.burst_ack_nack_received, "BURST ACK"),
            FR_TYPE.BURST_NACK.value: (self.arq_iss.burst_ack_nack_received, "BURST NACK"),
            FR_TYPE.CQ.value: (self.broadcasts.received_cq, "CQ"),
            FR_TYPE.FR_ACK.value: (self.arq_iss.frame_ack_received, "FRAME ACK"),
            FR_TYPE.FR_NACK.value: (self.arq_iss.frame_nack_received, "FRAME NACK"),
            FR_TYPE.FR_REPEAT.value: (self.arq_iss.burst_rpt_received, "REPEAT REQUEST"),
            FR_TYPE.PING_ACK.value: (self.ping.received_ping_ack, "PING ACK"),
            FR_TYPE.PING.value: (self.ping.received_ping, "PING"),
            FR_TYPE.QRV.value: (self.broadcasts.received_qrv, "QRV"),
            FR_TYPE.IS_WRITING.value: (self.broadcasts.received_is_writing, "IS_WRITING"),
            FR_TYPE.FEC.value: (self.data_broadcasts.received_fec, "FEC"),
            FR_TYPE.FEC_WAKEUP.value: (self.data_broadcasts.received_fec_wakeup, "FEC WAKEUP"),
        }

    def start(self):
        """Starts worker threads for transmit and receive operations."""
        threading.Thread(target=self.worker_transmit, name="Transmit Worker", daemon=True).start()
        threading.Thread(target=self.worker_receive, name="Receive Worker", daemon=True).start()

    def worker_transmit(self) -> None:
        """Dispatch incoming UI instructions for transmitting operations"""
        while True:
            command = self.data_queue_transmit.get()
            command.run(self.event_queue, MODEM_TRANSMIT_QUEUE)

    def worker_receive(self) -> None:
        """Queue received data for processing"""
        while True:
            data = self.data_queue_received.get()
            self.new_process_data(
                data['payload'],
                data['freedv'],
                data['bytes_per_frame'],
                data['snr'],
                data['frequency_offset'],
            )

    def new_process_data(self, bytes_out, freedv, bytes_per_frame: int, snr, offset) -> None:
        # get frame as dictionary
        deconstructed_frame = self.frame_factory.deconstruct(bytes_out)
        frametype = deconstructed_frame["frame_type_int"]

        if frametype not in self.FRAME_HANDLER:
            self.log.warning(
                "[Modem] ARQ - other frame type", frametype=FR_TYPE(frametype).name)
            return
        
        # instantiate handler
        handler_class = self.FRAME_HANDLER[frametype]['class']
        handler = handler_class(self.FRAME_HANDLER[frametype]['name'],
                                self.config,
                                self.states,
                                self.event_manager,
                                MODEM_TRANSMIT_QUEUE,
                                self.arq_sessions)

        activity = {
            "dxcallsign": deconstructed_frame["origin"],
            "direction": "received",
            "dxgrid": deconstructed_frame["gridsquare"],
            "snr": snr,
            "offset": offset,
            "activity_type": self.FRAME_HANDLER[frametype]['name']
        }
        self.states.add_activity(activity)
        handler.handle(deconstructed_frame, snr, offset, freedv, bytes_per_frame)

    def old_process_data(self, bytes_out, freedv, bytes_per_frame: int, snr) -> None:
        """
        Process incoming data and decide what to do with the frame.

        Args:
          bytes_out:
          freedv:
          bytes_per_frame:
          snr:

        Returns:

        """
        # get frame as dictionary
        deconstructed_frame = self.frame_factory.deconstruct(bytes_out)
        frametype = deconstructed_frame["frame_type_int"]

        if frametype not in self.rx_dispatcher:
            self.log.warning(
                "[Modem] ARQ - other frame type", frametype=FR_TYPE(frametype).name)
            return
        
        # Process frametypes requiring a different set of arguments.
        if FR_TYPE.BURST_51.value >= frametype >= FR_TYPE.BURST_01.value:
            self.arq_irs.arq_data_received(
                deconstructed_frame, bytes_per_frame, snr, freedv
            )

            # if we received the last frame of a burst or the last remaining rpt frame, do a modem unsync
            # if self.arq_rx_burst_buffer.count(None) <= 1 or (frame+1) == n_frames_per_burst:
            #    self.log.debug(f"[Modem] LAST FRAME OF BURST --> UNSYNC {frame+1}/{n_frames_per_burst}")
            #    self.c_lib.freedv_set_sync(freedv, 0)
            return

        # TESTFRAMES
        if frametype == FR_TYPE.TEST_FRAME.value:
            self.log.debug("[Modem] TESTFRAME RECEIVED", frame=deconstructed_frame)
            return

        # Process frames "known" by rx_dispatcher
        # self.log.debug(f"[Modem] {self.rx_dispatcher[frametype][1]} RECEIVED....")
        self.rx_dispatcher[frametype][0](deconstructed_frame, snr)

    def get_id_from_frame(self, data):
        if data[:1] in [FR_TYPE.ARQ_DC_OPEN_N, FR_TYPE.ARQ_DC_OPEN_W]:
            return data[13:14]
        return None

    def initialize_arq_instance(self):
        self.arq = ARQ(self.config, self.event_queue, self.states)
        self.arq_irs = IRS(self.config, self.event_queue, self.states)
        self.arq_iss = ISS(self.config, self.event_queue, self.states)
        self.arq_session = SESSION(self.config, self.event_queue, self.states)

        return {
            'arq': self.arq,
            'arq_irs': self.arq_irs,
            'arq_iss': self.arq_iss,
            'arq_session': self.arq_session
        }

    def initialize_arq_transmission_irs(self, data):
        if id := self.get_id_from_frame(data):
            instance = self.initialize_arq_instance()
            self.states.register_arq_instance_by_id(id, instance)
            instance['arq_irs'].arq_received_data_channel_opener()
