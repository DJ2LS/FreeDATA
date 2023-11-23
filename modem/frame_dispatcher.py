"""
FRAME DISPATCHER - We are dispatching the received frames to the needed functions


"""
import threading
import helpers
import structlog
from modem_frametypes import FRAME_TYPE as FR_TYPE
import event_manager
from queues import DATA_QUEUE_RECEIVED, DATA_QUEUE_TRANSMIT

from data_handler_broadcasts import BROADCAST
from data_handler_data_broadcasts import DATABROADCAST
from data_handler_ping import PING

from protocol_arq_iss import ISS
from protocol_arq_irs import IRS
from protocol_arq import ARQ
from protocol_arq_session import SESSION


class DISPATCHER():

    def __init__(self, config, event_queue, states):
        print("loading frame dispatcher.....")
        self.config = config
        self.event_queue = event_queue
        self.states = states

        self._initialize_handlers(config, event_queue, states)
        self._initialize_dispatchers()
        self._initialize_queues()

    def _initialize_handlers(self, config, event_queue, states):
        """Initializes various data handlers."""
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
        self.command_dispatcher = {
            # "CONNECT": (self.arq_session_handler, "CONNECT"),
            "CQ": (self.broadcasts.transmit_cq, "CQ"),
            "DISCONNECT": (self.arq_session.close_session, "DISCONNECT"),
            "SEND_TEST_FRAME": (self.broadcasts.send_test_frame, "TEST"),
            "STOP": (self.arq.stop_transmission, "STOP"),
        }

    def _initialize_queues(self):
        """Initializes data queues."""
        self.data_queue_transmit = DATA_QUEUE_TRANSMIT
        self.data_queue_received = DATA_QUEUE_RECEIVED

    def _start_worker_threads(self):
        """Starts worker threads for transmit and receive operations."""
        threading.Thread(target=self.worker_transmit, name="Transmit Worker", daemon=True).start()
        threading.Thread(target=self.worker_receive, name="Receive Worker", daemon=True).start()

    def start(self):
        self._start_worker_threads()

    def worker_transmit(self) -> None:
        """Dispatch incoming UI instructions for transmitting operations"""
        while True:
            data = self.data_queue_transmit.get()
            self.log.debug(
                    "[Modem] TX DISPATCHER - got a transmit command",
                    command=data,
                )

            

            # Dispatch commands known to command_dispatcher
            if data[0] in self.command_dispatcher:
                self.log.debug(f"[Modem] TX {self.command_dispatcher[data[0]][1]}...")
                self.command_dispatcher[data[0]][0]()

            # Dispatch commands that need more arguments.
            elif data[0] == "CONNECT":
                # [1] mycallsign
                # [2] dxcallsign
                self.arq.arq_session_handler(data[1], data[2])

            elif data[0] == "PING":
                # [1] mycallsign // this is being injected as None
                # [2] dxcallsign
                mycallsign = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
                self.ping.transmit_ping(mycallsign, data[2])

            elif data[0] == "ARQ_RAW":
                # [1] DATA_OUT bytes
                # [2] self.transmission_uuid str
                # [3] mycallsign with ssid str
                # [4] dxcallsign with ssid str
                self.arq_iss.open_dc_and_transmit(data[1], data[2], data[3], data[4])

            elif data[0] == "FEC_IS_WRITING":
                # [1] DATA_OUT bytes
                # [2] MODE str datac0/1/3...
                self.broadcasts.send_fec_is_writing(data[1])

            elif data[0] == "FEC":
                # [1] WAKEUP bool
                # [2] MODE str datac0/1/3...
                # [3] PAYLOAD
                # [4] MYCALLSIGN
                self.broadcasts.send_fec(data[1], data[2], data[3], data[4])
            else:
                self.log.error(
                    "[Modem] worker_transmit: received invalid command:", data=data
                )

    def worker_receive(self) -> None:
        """Queue received data for processing"""
        while True:
            data = self.data_queue_received.get()
            # [0] bytes
            # [1] freedv instance
            # [2] bytes_per_frame
            # [3] snr
            self.process_data(
                bytes_out=data[0], freedv=data[1], bytes_per_frame=data[2], snr=data[3]
            )

    def process_data(self, bytes_out, freedv, bytes_per_frame: int, snr) -> None:
        """
        Process incoming data and decide what to do with the frame.

        Args:
          bytes_out:
          freedv:
          bytes_per_frame:
          snr:

        Returns:

        """

        if self.check_if_valid_frame(bytes_out):
            frametype = int.from_bytes(bytes(bytes_out[:1]), "big")
            # Dispatch activity based on received frametype
            if frametype in self.rx_dispatcher:
                # Process frames "known" by rx_dispatcher
                # self.log.debug(f"[Modem] {self.rx_dispatcher[frametype][1]} RECEIVED....")
                self.rx_dispatcher[frametype][0](bytes_out[:-2], snr)

            # Process frametypes requiring a different set of arguments.
            elif FR_TYPE.BURST_51.value >= frametype >= FR_TYPE.BURST_01.value:
                # get snr of received data
                # FIXME find a fix for this - after moving to classes, this no longer works
                # snr = self.calculate_snr(freedv)
                self.log.debug("[Modem] RX SNR", snr=snr)
                # send payload data to arq checker without CRC16
                self.arq_irs.arq_data_received(
                    bytes(bytes_out[:-2]), bytes_per_frame, snr, freedv
                )

                # if we received the last frame of a burst or the last remaining rpt frame, do a modem unsync
                # if self.arq_rx_burst_buffer.count(None) <= 1 or (frame+1) == n_frames_per_burst:
                #    self.log.debug(f"[Modem] LAST FRAME OF BURST --> UNSYNC {frame+1}/{n_frames_per_burst}")
                #    self.c_lib.freedv_set_sync(freedv, 0)

            # TESTFRAMES
            elif frametype == FR_TYPE.TEST_FRAME.value:
                self.log.debug("[Modem] TESTFRAME RECEIVED", frame=bytes_out[:])

            # Unknown frame type
            else:
                self.log.warning(
                    "[Modem] ARQ - other frame type", frametype=FR_TYPE(frametype).name
                )

        else:
            # for debugging purposes to receive all data
            self.log.debug(
                "[Modem] Foreign frame received",
                frame=bytes_out[:-2].hex(),
                frame_type=FR_TYPE(int.from_bytes(bytes_out[:1], byteorder="big")).name,
            )

    def check_if_valid_frame(self, bytes_out):
        # Process data only if broadcast or we are the receiver
        # bytes_out[1:4] == callsign check for signalling frames,
        # bytes_out[2:5] == transmission
        # we could also create an own function, which returns True.
        frametype = int.from_bytes(bytes(bytes_out[:1]), "big")

        # check for callsign CRC
        _valid1, _ = helpers.check_callsign(self.arq.mycallsign, bytes(bytes_out[1:4]), self.arq.ssid_list)
        _valid2, _ = helpers.check_callsign(self.arq.mycallsign, bytes(bytes_out[2:5]), self.arq.ssid_list)
        # check for session ID
        _valid3 = helpers.check_session_id(self.arq.session_id, bytes(bytes_out[1:2]))  # signalling frames
        _valid4 = helpers.check_session_id(self.arq.session_id, bytes(bytes_out[2:3]))  # arq data frames
        if (
                _valid1
                or _valid2
                or _valid3
                or _valid4
                or frametype
                in [
            FR_TYPE.CQ.value,
            FR_TYPE.QRV.value,
            FR_TYPE.PING.value,
            FR_TYPE.BEACON.value,
            FR_TYPE.IS_WRITING.value,
            FR_TYPE.FEC.value,
            FR_TYPE.FEC_WAKEUP.value,
        ]
        ):
            return True
        return False

    def get_id_from_frame(self, data):
        if data[:1] in [FR_TYPE.ARQ_DC_OPEN_N, FR_TYPE.ARQ_DC_OPEN_W]:
            session_id = data[13:14]
            return session_id
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
            instance['arq_irs'].arq_received_data_channel_opener