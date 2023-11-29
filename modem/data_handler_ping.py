import time
from modem_frametypes import FRAME_TYPE as FR_TYPE
from codec2 import FREEDV_MODE
import helpers
import uuid
import structlog
from data_handler import DATA
class PING(DATA):
    def __init__(self, config, event_queue, states):
        super().__init__(config, event_queue, states)

        self.log = structlog.get_logger("DHPING")
        self.states = states
        self.event_queue = event_queue
        self.config = config

    def received_ping(self, deconstructed_frame: list, snr) -> None:
        """
        Called if we received a ping

        Args:
          data_in:bytes:

        """
        destination_crc = deconstructed_frame["destination_crc"]
        origin_crc = deconstructed_frame["origin_crc"]
        origin = deconstructed_frame["origin"]

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.config['STATION']['mycall'], destination_crc, self.config['STATION']['ssid_list'])
        if not valid:
            # PING packet not for me.
            self.log.debug("[Modem] received_ping: ping not for this station.")
            return

        self.dxcallsign_crc = origin_crc
        self.dxcallsign = origin
        self.log.info(
            f"[Modem] PING REQ from [{origin}] to [{mycallsign}]",
            snr=snr,
        )

        self.dxgrid = ""
        helpers.add_to_heard_stations(
            origin,
            self.dxgrid,
            "PING",
            snr,
            -999, # TODO we don't have the offset available here yet...
            self.states.radio_frequency,
            self.states.heard_stations
        )

        self.event_queue.put({
            "freedata": "modem-message",
            "ping": "received",
            "uuid": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "dxgrid": self.dxgrid,
            "dxcallsign": origin,
            "mycallsign": mycallsign,
            "snr": str(snr),
        })
        
        self.transmit_ping_ack(snr)

    def transmit_ping_ack(self, snr):
        """

        transmit a ping ack frame
        called by def received_ping
        """

        self.log.warning('DATA_HANDLER_PING: REVISE PING ACK!')
        return

        ping_frame = bytearray(self.length_sig0_frame)
        ping_frame[:1] = bytes([FR_TYPE.PING_ACK.value])
        ping_frame[1:4] = self.dxcallsign_crc
        ping_frame[4:7] = self.mycallsign_crc
        ping_frame[7:11] = helpers.encode_grid(self.mygrid)
        ping_frame[13:14] = helpers.snr_to_bytes(snr)

        if self.enable_fsk:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.sig0.value)

    def received_ping_ack(self, data_in: bytes, snr) -> None:
        """
        Called if a PING ack has been received
        Args:
          data_in:bytes:

        """

        # check if we received correct ping
        # check if callsign ssid override
        _valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4], self.ssid_list)
        if _valid:

            self.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")
            dxsnr = helpers.snr_from_bytes(data_in[13:14])
            self.send_data_to_socket_queue(
                freedata="modem-message",
                ping="acknowledge",
                uuid=str(uuid.uuid4()),
                timestamp=int(time.time()),
                dxgrid=str(self.dxgrid, "UTF-8"),
                dxcallsign=str(self.dxcallsign, "UTF-8"),
                mycallsign=str(mycallsign, "UTF-8"),
                snr=str(snr),
                dxsnr=str(dxsnr)
            )
            # combined_snr = own rx snr / snr on dx side
            combined_snr = f"{snr}/{dxsnr}"
            helpers.add_to_heard_stations(
                self.dxcallsign,
                self.dxgrid,
                "PING-ACK",
                combined_snr,
                self.modem_frequency_offset,
                self.states.radio_frequency,
                self.states.heard_stations
            )

            self.log.info(
                "[Modem] PING ACK ["
                + str(mycallsign, "UTF-8")
                + "] >|< ["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                snr=snr,
                dxsnr=dxsnr,
            )
            self.states.set("is_modem_busy", False)
        else:
            self.log.info(
                "[Modem] FOREIGN PING ACK ["
                + str(self.mycallsign, "UTF-8")
                + "] ??? ["
                + str(bytes(data_in[4:7]), "UTF-8")
                + "]",
                snr=snr,
            )
