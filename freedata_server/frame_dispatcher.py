"""
FRAME DISPATCHER - We are dispatching the received frames to the needed functions


"""

import threading
import structlog
from freedata_server.modem_frametypes import FRAME_TYPE as FR_TYPE
from freedata_server.data_frame_factory import DataFrameFactory

from freedata_server.frame_handler import FrameHandler
from freedata_server.frame_handler_ping import PingFrameHandler
from freedata_server.frame_handler_cq import CQFrameHandler
from freedata_server.frame_handler_arq_session import ARQFrameHandler
from freedata_server.frame_handler_p2p_connection import P2PConnectionFrameHandler
from freedata_server.frame_handler_beacon import BeaconFrameHandler


class DISPATCHER:
    """Dispatches received frames to appropriate handlers.

    This class manages the dispatching of received frames to the correct
    handler based on the frame type. It initializes frame handlers, starts
    worker threads for receiving and processing frames, and provides a
    mechanism for stopping the dispatcher.
    """

    FRAME_HANDLER = {
        FR_TYPE.ARQ_SESSION_OPEN_ACK.value: {"class": ARQFrameHandler, "name": "ARQ OPEN ACK"},
        FR_TYPE.ARQ_SESSION_OPEN.value: {"class": ARQFrameHandler, "name": "ARQ Data Channel Open"},
        FR_TYPE.ARQ_SESSION_INFO_ACK.value: {"class": ARQFrameHandler, "name": "ARQ INFO ACK"},
        FR_TYPE.ARQ_SESSION_INFO.value: {"class": ARQFrameHandler, "name": "ARQ Data Channel Info"},
        FR_TYPE.P2P_CONNECTION_CONNECT.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection CONNECT",
        },
        FR_TYPE.P2P_CONNECTION_CONNECT_ACK.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection CONNECT ACK",
        },
        FR_TYPE.P2P_CONNECTION_DISCONNECT.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection DISCONNECT",
        },
        FR_TYPE.P2P_CONNECTION_DISCONNECT_ACK.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection DISCONNECT ACK",
        },
        FR_TYPE.P2P_CONNECTION_PAYLOAD.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection PAYLOAD",
        },
        FR_TYPE.P2P_CONNECTION_PAYLOAD_ACK.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection PAYLOAD ACK",
        },
        FR_TYPE.P2P_CONNECTION_HEARTBEAT.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection HEARTBEAT",
        },
        FR_TYPE.P2P_CONNECTION_HEARTBEAT_ACK.value: {
            "class": P2PConnectionFrameHandler,
            "name": "P2P Connection HEARTBEAT ACK",
        },
        FR_TYPE.ARQ_STOP.value: {"class": ARQFrameHandler, "name": "ARQ STOP"},
        FR_TYPE.ARQ_STOP_ACK.value: {"class": ARQFrameHandler, "name": "ARQ STOP ACK"},
        FR_TYPE.BEACON.value: {"class": BeaconFrameHandler, "name": "BEACON"},
        FR_TYPE.ARQ_BURST_FRAME.value: {"class": ARQFrameHandler, "name": "BURST FRAME"},
        FR_TYPE.ARQ_BURST_ACK.value: {"class": ARQFrameHandler, "name": "BURST ACK"},
        FR_TYPE.CQ.value: {"class": CQFrameHandler, "name": "CQ"},
        FR_TYPE.PING_ACK.value: {"class": FrameHandler, "name": "PING ACK"},
        FR_TYPE.PING.value: {"class": PingFrameHandler, "name": "PING"},
        FR_TYPE.QRV.value: {"class": FrameHandler, "name": "QRV"},
        # FR_TYPE.IS_WRITING.value: {"class": FrameHandler, "name": "IS_WRITING"},
        # FR_TYPE.FEC.value: {"class": FrameHandler, "name":  "FEC"},
        # FR_TYPE.FEC_WAKEUP.value: {"class": FrameHandler, "name":  "FEC WAKEUP"},
    }

    def __init__(self, ctx):
        """Initializes the frame dispatcher.

        This method sets up the frame dispatcher with the provided
        configuration, event manager, state manager, and modem. It
        initializes frame handlers and starts the receive worker thread.

        Args:
            config (dict): The configuration dictionary.
            event_manager (EventManager): The event manager object.
            states (StateManager): The state manager object.
            modem: The modem object.
        """
        self.log = structlog.get_logger("frame_dispatcher")
        self.ctx = ctx
        self.log.info("loading frame dispatcher.....\n")
        self.stop_event = threading.Event()

        self.frame_factory = DataFrameFactory(self.ctx)

        self.arq_sessions = []

    def start(self):
        """Starts worker threads for transmit and receive operations."""
        threading.Thread(target=self.worker_receive, name="Receive Worker", daemon=True).start()

    def stop(self):
        self.stop_event.set()

    def worker_receive(self) -> None:
        """Queue received data for processing"""
        while not self.stop_event.is_set():
            try:
                data = self.ctx.rf_modem.data_queue_received.get(timeout=1)
                if data:
                    self.process_data(
                        data["payload"],
                        data["freedv"],
                        data["bytes_per_frame"],
                        data["snr"],
                        data["frequency_offset"],
                        data["mode_name"],
                    )
            except Exception:
                continue

    def process_data(
        self, bytes_out, freedv, bytes_per_frame: int, snr, frequency_offset, mode_name
    ) -> None:
        """Processes received data frames.

        This method deconstructs the received data into a frame dictionary,
        identifies the frame type, and dispatches the frame to the
        appropriate handler based on its type. It logs warnings for
        unknown frame types.

        Args:
            bytes_out (bytes): The raw frame data.
            freedv: The FreeDV instance.
            bytes_per_frame (int): The number of bytes per frame.
            snr (float): The signal-to-noise ratio of the received frame.
            frequency_offset (float): The frequency offset of the received frame.
            mode_name (str): The name of the FreeDV mode.
        """
        # get frame as dictionary
        deconstructed_frame = self.frame_factory.deconstruct(bytes_out, mode_name=mode_name)
        frametype = deconstructed_frame["frame_type_int"]
        if frametype not in self.FRAME_HANDLER:
            self.log.warning("[DISPATCHER] unknown burst", frametype=FR_TYPE(frametype).name)
            return

        # instantiate handler
        handler_class = self.FRAME_HANDLER[frametype]["class"]
        handler: FrameHandler = handler_class(self.ctx, self.FRAME_HANDLER[frametype]["name"])
        handler.handle(deconstructed_frame, snr, frequency_offset, freedv, bytes_per_frame)

    def get_id_from_frame(self, data):
        """Extracts the session ID from an ARQ_SESSION_OPEN frame.

        This method checks if the provided data represents an
        ARQ_SESSION_OPEN frame and, if so, extracts and returns the session
        ID. Otherwise, it returns None. This method is currently not used
        in the code.

        Args:
            data (bytes): The frame data.

        Returns:
            bytes or None: The session ID if the frame is an ARQ_SESSION_OPEN
            frame, None otherwise.
        """
        if data[:1] == FR_TYPE.ARQ_SESSION_OPEN:
            return data[13:14]
        return None
