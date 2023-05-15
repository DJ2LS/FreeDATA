import structlog
import threading
import helpers
import time
import modem
import base64
from static import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, TNC
import sock
import ujson as json


class broadcastHandler:
    """Terminal Node Controller for FreeDATA"""

    log = structlog.get_logger("BROADCAST")

    def __init__(self) -> None:
        self.fec_wakeup_callsign = bytes()
        self.longest_duration = 6

    def received_fec_wakeup(self, data_in: bytes):
        self.fec_wakeup_callsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        mode = int.from_bytes(bytes(data_in[7:8]), "big")
        bursts = int.from_bytes(bytes(data_in[8:9]), "big")

        modem.RECEIVE_DATAC4 = True

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            fec="wakeup",
            mode=mode,
            bursts=bursts,
            dxcallsign=str(self.fec_wakeup_callsign, "UTF-8")
        )

        timeout = time.time() + (self.longest_duration * bursts) + 2
        self.log.info(
            "[TNC] FRAME WAKEUP RCVD ["
            + str(self.fec_wakeup_callsign, "UTF-8")
            + "] ", mode=mode, bursts=bursts, timeout=timeout,
        )

        while time.time() < timeout:
            threading.Event().wait(0.01)

        self.log.info(
            "[TNC] closing broadcast slot ["
            + str(self.fec_wakeup_callsign, "UTF-8")
            + "] ", mode=mode, bursts=bursts,
        )
        # TODO: We need a dynamic way of modifying this
        modem.RECEIVE_DATAC4 = False
        self.fec_wakeup_callsign = bytes()


    def received_fec(self, data_in: bytes):
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            fec="broadcast",
            dxcallsign=str(self.fec_wakeup_callsign, "UTF-8"),
            data=base64.b64encode(data_in[1:]).decode("UTF-8")
        )

        self.log.info("[TNC] FEC DATA RCVD")

    def send_data_to_socket_queue(self, **jsondata):
        """
        Send information to the UI via JSON and the sock.SOCKET_QUEUE.

        Args:
          Dictionary containing the data to be sent, in the format:
          key=value, for each item. E.g.:
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="received",
                status="success",
                uuid=self.transmission_uuid,
                timestamp=timestamp,
                mycallsign=str(self.mycallsign, "UTF-8"),
                dxcallsign=str(Station.dxcallsign, "UTF-8"),
                dxgrid=str(Station.dxgrid, "UTF-8"),
                data=base64_data,
            )
        """

        # add mycallsign and dxcallsign to network message if they not exist
        # and make sure we are not overwrite them if they exist
        try:
            if "mycallsign" not in jsondata:
                jsondata["mycallsign"] = str(self.mycallsign, "UTF-8")
            if "dxcallsign" not in jsondata:
                jsondata["dxcallsign"] = str(Station.dxcallsign, "UTF-8")
        except Exception as e:
            self.log.debug("[TNC] error adding callsigns to network message", e=e)

        # run json dumps
        json_data_out = json.dumps(jsondata)

        self.log.debug("[TNC] send_data_to_socket_queue:", jsondata=json_data_out)
        # finally push data to our network queue
        sock.SOCKET_QUEUE.put(json_data_out)