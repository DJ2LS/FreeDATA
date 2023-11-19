
import time
import helpers
from codec2 import FREEDV_MODE
from queues import MODEM_TRANSMIT_QUEUE
from modem_frametypes import FRAME_TYPE as FR_TYPE

from data_handler_arq import ARQ


class SESSION(ARQ):

    def __init__(self, config, event_queue, states):
        super().__init__(config, event_queue, states)

    def received_session_close(self, data_in: bytes, snr):
        """
        Closes the session when a close session frame is received and
        the DXCALLSIGN_CRC matches the remote station participating in the session.

        Args:
          data_in:bytes:

        """
        # We've arrived here from process_data which already checked that the frame
        # is intended for this station.
        # Close the session if the CRC matches the remote station in static.
        _valid_crc, mycallsign = helpers.check_callsign(self.mycallsign, bytes(data_in[2:5]), self.ssid_list)
        _valid_session = helpers.check_session_id(self.session_id, bytes(data_in[1:2]))
        if (_valid_crc or _valid_session) and self.states.arq_session_state not in ["disconnected"]:
            self.states.set("arq_session_state", "disconnected")
            self.dxgrid = b'------'
            helpers.add_to_heard_stations(
                self.dxcallsign,
                self.dxgrid,
                "DATA",
                snr,
                self.modem_frequency_offset,
                self.states.radio_frequency,
                self.states.heard_stations
            )
            self.log.info(
                "[Modem] SESSION ["
                + str(self.mycallsign, "UTF-8")
                + "]<<X>>["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                self.states.arq_session_state,
            )

            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="session",
                status="close",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            self.IS_ARQ_SESSION_MASTER = False
            self.states.is_arq_session = False
            self.arq_cleanup()

    def transmit_session_heartbeat(self) -> None:
        """Send ARQ sesion heartbeat while connected"""
        # self.states.is_arq_session = True
        # self.states.set("is_modem_busy", True)
        # self.states.set("arq_session_state", "connected")

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_HB.value])
        connection_frame[1:2] = self.session_id

        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="session",
            status="connected",
            heartbeat="transmitting",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

    def received_session_heartbeat(self, data_in: bytes, snr) -> None:
        """
        Received an ARQ session heartbeat, record and update state accordingly.
        Args:
          data_in:bytes:

        """
        # Accept session data if the DXCALLSIGN_CRC matches the station in static or session id.
        _valid_crc, _ = helpers.check_callsign(self.dxcallsign, bytes(data_in[4:7]), self.ssid_list)
        _valid_session = helpers.check_session_id(self.session_id, bytes(data_in[1:2]))
        if _valid_crc or _valid_session and self.states.arq_session_state in ["connected", "connecting"]:
            self.log.debug("[Modem] Received session heartbeat")
            self.dxgrid = b'------'
            helpers.add_to_heard_stations(
                self.dxcallsign,
                self.dxgrid,
                "SESSION-HB",
                snr,
                self.modem_frequency_offset,
                self.states.radio_frequency,
                self.states.heard_stations
            )

            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="session",
                status="connected",
                heartbeat="received",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            self.states.is_arq_session = True
            self.states.set("arq_session_state", "connected")
            self.states.set("is_modem_busy", True)

            # Update the timeout timestamps
            self.arq_session_last_received = int(time.time())
            self.data_channel_last_received = int(time.time())
            # transmit session heartbeat only
            # -> if not session master
            # --> this will be triggered by heartbeat watchdog
            # -> if not during a file transfer
            # -> if ARQ_SESSION_STATE != disconnecting, disconnected, failed
            # --> to avoid heartbeat toggle loops while disconnecting
            if (
                    not self.IS_ARQ_SESSION_MASTER
                    and not self.arq_file_transfer
                    and self.states.arq_session_state != 'disconnecting'
                    and self.states.arq_session_state != 'disconnected'
                    and self.states.arq_session_state != 'failed'
            ):
                self.transmit_session_heartbeat()


    def close_session(self) -> None:
        """Close the ARQ session"""
        self.states.set("arq_session_state", "disconnecting")

        self.log.info(
            "[Modem] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]<<X>>["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            self.states.arq_session_state,
        )

        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="session",
            status="close",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.IS_ARQ_SESSION_MASTER = False
        self.states.is_arq_session = False

        # we need to send disconnect frame before doing arq cleanup
        # we would lose our session id then
        self.send_disconnect_frame()

        # transmit morse identifier if configured
        if self.enable_morse_identifier:
            MODEM_TRANSMIT_QUEUE.put(["morse", 1, 0, self.mycallsign])
        self.arq_cleanup()

    def received_session_opener(self, data_in: bytes, snr) -> None:
        """
        Received a session open request packet.

        Args:
          data_in:bytes:
        """
        # if we don't want to respond to calls, return False
        if not self.respond_to_call:
            return False

        # ignore channel opener if already in ARQ STATE
        # use case: Station A is connecting to Station B while
        # Station B already tries connecting to Station A.
        # For avoiding ignoring repeated connect request in case of packet loss
        # we are only ignoring packets in case we are ISS
        if self.states.is_arq_session and self.IS_ARQ_SESSION_MASTER:
            return False

        self.IS_ARQ_SESSION_MASTER = False
        self.states.set("arq_session_state", "connecting")

        # Update arq_session timestamp
        self.arq_session_last_received = int(time.time())

        self.session_id = bytes(data_in[1:2])
        self.dxcallsign_crc = bytes(data_in[5:8])
        self.dxcallsign = helpers.bytes_to_callsign(bytes(data_in[8:14]))
        self.states.set("dxcallsign", self.dxcallsign)

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[2:5], self.ssid_list)
        self.mycallsign = mycallsign
        self.dxgrid = b'------'
        helpers.add_to_heard_stations(
            self.dxcallsign,
            self.dxgrid,
            "DATA",
            snr,
            self.modem_frequency_offset,
            self.states.radio_frequency,
            self.states.heard_stations
        )
        self.log.info(
            "[Modem] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]>>|<<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            self.states.arq_session_state,
        )
        self.states.is_arq_session = True
        self.states.set("is_modem_busy", True)

        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="session",
            status="connected",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.transmit_session_heartbeat()
