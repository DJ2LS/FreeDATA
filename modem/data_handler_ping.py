import time
from modem_frametypes import FRAME_TYPE as FR_TYPE
from codec2 import FREEDV_MODE
import helpers
import uuid

class PING:
    def __init__(self):
        pass

    # ---------- PING
    def transmit_ping(self, mycallsign: bytes, dxcallsign: bytes) -> None:
        """
        Funktion for controlling pings
        Args:
          mycallsign:bytes:
          dxcallsign:bytes:

        """
        # check if specific callsign is set with different SSID than the Modem is initialized
        try:
            mycallsign = helpers.callsign_to_bytes(mycallsign)
            mycallsign = helpers.bytes_to_callsign(mycallsign)
        except Exception:
            mycallsign = self.mycallsign

        if not str(dxcallsign).strip():
            self.log.warning("[Modem] Missing required callsign", dxcallsign=dxcallsign)
            return

        # additional step for being sure our callsign is correctly
        # in case we are not getting a station ssid
        # then we are forcing a station ssid = 0
        dxcallsign = helpers.callsign_to_bytes(dxcallsign)
        dxcallsign = helpers.bytes_to_callsign(dxcallsign)

        self.dxcallsign = dxcallsign
        self.dxcallsign_crc = helpers.get_crc_24(self.dxcallsign)
        self.send_data_to_socket_queue(
            freedata="modem-message",
            ping="transmitting",
            dxcallsign=str(dxcallsign, "UTF-8"),
        )
        self.log.info(
            "[Modem] PING REQ ["
            + mycallsign
            + "] >>> ["
            + str(dxcallsign, "UTF-8")
            + "]"
        )

        ping_frame = bytearray(self.length_sig0_frame)
        ping_frame[:1] = bytes([FR_TYPE.PING.value])
        ping_frame[1:4] = self.dxcallsign_crc
        ping_frame[4:7] = helpers.get_crc_24(mycallsign)
        ping_frame[7:13] = helpers.callsign_to_bytes(mycallsign)

        if self.enable_fsk:
            self.log.info("[Modem] ENABLE FSK", state=self.enable_fsk)
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.sig0.value)

    def received_ping(self, data_in: bytes, snr) -> None:
        """
        Called if we received a ping

        Args:
          data_in:bytes:

        """
        dxcallsign_crc = bytes(data_in[4:7])
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[7:13]))

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4], self.ssid_list)
        if not valid:
            # PING packet not for me.
            self.log.debug("[Modem] received_ping: ping not for this station.")
            return

        self.dxcallsign_crc = dxcallsign_crc
        self.dxcallsign = dxcallsign
        self.log.info(
            "[Modem] PING REQ ["
            + str(mycallsign, "UTF-8")
            + "] <<< ["
            + str(dxcallsign, "UTF-8")
            + "]",
            snr=snr,
        )

        self.dxgrid = b'------'
        helpers.add_to_heard_stations(
            dxcallsign,
            self.dxgrid,
            "PING",
            snr,
            self.modem_frequency_offset,
            self.states.radio_frequency,
            self.states.heard_stations
        )

        self.send_data_to_socket_queue(
            freedata="modem-message",
            ping="received",
            uuid=str(uuid.uuid4()),
            timestamp=int(time.time()),
            dxgrid=str(self.dxgrid, "UTF-8"),
            dxcallsign=str(dxcallsign, "UTF-8"),
            mycallsign=str(mycallsign, "UTF-8"),
            snr=str(snr),
        )
        if self.respond_to_call:
            self.transmit_ping_ack(snr)

    def transmit_ping_ack(self, snr):
        """

        transmit a ping ack frame
        called by def received_ping
        """
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
