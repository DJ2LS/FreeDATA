import time
from modem_frametypes import FRAME_TYPE as FR_TYPE
from codec2 import FREEDV_MODE
from queues import MODEM_TRANSMIT_QUEUE
import threading
import helpers
import codec2
import modem
from random import randrange
import uuid
import structlog
from data_handler_helpers import enqueue_frame_for_tx, send_data_to_socket_queue

TESTMODE = False

class BROADCAST:

    def __init__(self, config, event_queue, states):
        self.log = structlog.get_logger("DHBC")
        self.states = states
        self.event_queue = event_queue
        self.config = config

        self.beacon_interval = 0
        self.beacon_interval_timer = 0
        self.beacon_paused = False
        self.beacon_thread = threading.Thread(
            target=self.run_beacon, name="watchdog", daemon=True
        )
        self.beacon_thread.start()


        # length of signalling frame
        self.length_sig0_frame = 14
        self.modem_frequency_offset = 0

        # load config
        self.mycallsign = config['STATION']['mycall']
        self.myssid = config['STATION']['myssid']
        self.mycallsign += "-" + str(self.myssid)
        encoded_call = helpers.callsign_to_bytes(self.mycallsign)
        self.mycallsign = helpers.bytes_to_callsign(encoded_call)
        self.mygrid = config['STATION']['mygrid']
        self.enable_fsk = config['MODEM']['enable_fsk']
        self.respond_to_cq = config['MODEM']['respond_to_cq']
        self.respond_to_call = True

        self.duration_datac13 = 2.0
        self.duration_sig1_frame = self.duration_datac13


    def send_test_frame(self) -> None:
        """Send an empty test frame"""
        test_frame = bytearray(126)
        test_frame[:1] = bytes([FR_TYPE.TEST_FRAME.value])
        enqueue_frame_for_tx(
            frame_to_tx=[test_frame], c2_mode=FREEDV_MODE.datac13.value
        )

    def send_fec(self, mode, wakeup, payload, mycallsign):
        """Send an empty test frame"""

        mode_int = codec2.freedv_get_mode_value_by_name(mode)
        payload_per_frame = modem.get_bytes_per_frame(mode_int) - 2
        fec_payload_length = payload_per_frame - 1

        # check callsign
        if mycallsign in [None]:
            mycallsign = self.mycallsign
        mycallsign = helpers.callsign_to_bytes(mycallsign)
        mycallsign = helpers.bytes_to_callsign(mycallsign)

        if wakeup:
            mode_int_wakeup = codec2.freedv_get_mode_value_by_name("sig0")
            payload_per_wakeup_frame = modem.get_bytes_per_frame(mode_int_wakeup) - 2
            fec_wakeup_frame = bytearray(payload_per_wakeup_frame)
            fec_wakeup_frame[:1] = bytes([FR_TYPE.FEC_WAKEUP.value])
            fec_wakeup_frame[1:7] = helpers.callsign_to_bytes(mycallsign)
            fec_wakeup_frame[7:8] = bytes([mode_int])
            fec_wakeup_frame[8:9] = bytes([1]) # n payload bursts
            print(mode_int_wakeup)

            enqueue_frame_for_tx(
                frame_to_tx=[fec_wakeup_frame], c2_mode=codec2.FREEDV_MODE["sig1"].value
            )
        time.sleep(1)
        fec_frame = bytearray(payload_per_frame)
        fec_frame[:1] = bytes([FR_TYPE.FEC.value])
        fec_frame[1:payload_per_frame] = bytes(payload[:fec_payload_length])
        enqueue_frame_for_tx(
            frame_to_tx=[fec_frame], c2_mode=codec2.FREEDV_MODE[mode].value
        )

    def send_fec_is_writing(self, mycallsign) -> None:
        """Send an fec is writing frame"""

        fec_frame = bytearray(14)
        fec_frame[:1] = bytes([FR_TYPE.IS_WRITING.value])
        fec_frame[1:7] = helpers.callsign_to_bytes(mycallsign)

        # send burst only if channel not busy - but without waiting
        # otherwise burst will be dropped
        if not self.states.channel_busy and not self.states.is_transmitting:
            enqueue_frame_for_tx(
                frame_to_tx=[fec_frame], c2_mode=codec2.FREEDV_MODE["sig0"].value
            )
        else:
            return False



    def transmit_cq(self) -> None:
        """
        Transmit a CQ
        Args:
            self

        Returns:
            Nothing
        """
        self.log.info("[Modem] CQ CQ CQ")

        send_data_to_socket_queue(
            freedata="modem-message",
            cq="transmitting",
            mycallsign=str(self.mycallsign, "UTF-8"),
            dxcallsign="None",
        )


        cq_frame = bytearray(self.length_sig0_frame)
        cq_frame[:1] = bytes([FR_TYPE.CQ.value])
        cq_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
        cq_frame[7:11] = helpers.encode_grid(self.mygrid)

        self.log.debug("[Modem] CQ Frame:", data=[cq_frame])

        if self.enable_fsk:
            self.log.info("[Modem] ENABLE FSK", state=self.enable_fsk)
            enqueue_frame_for_tx([cq_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            enqueue_frame_for_tx([cq_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

    def received_cq(self, data_in: bytes, snr) -> None:
        """
        Called when we receive a CQ frame
        Args:
          data_in:bytes:

        Returns:
            Nothing
        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        self.log.debug("[Modem] received_cq:", dxcallsign=dxcallsign)
        self.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")

        send_data_to_socket_queue(
            freedata="modem-message",
            cq="received",
            mycallsign=str(self.mycallsign, "UTF-8"),
            dxcallsign=str(dxcallsign, "UTF-8"),
            dxgrid=str(self.dxgrid, "UTF-8"),
        )

        self.log.info(
            "[Modem] CQ RCVD ["
            + str(dxcallsign, "UTF-8")
            + "]["
            + str(self.dxgrid, "UTF-8")
            + "] ",
            snr=snr,
        )
        helpers.add_to_heard_stations(
            dxcallsign,
            self.dxgrid,
            "CQ CQ CQ",
            snr,
            self.modem_frequency_offset,
            self.states.radio_frequency,
            self.states.heard_stations
        )

        if self.respond_to_cq and self.respond_to_call:
            self.transmit_qrv(dxcallsign, snr)

    def transmit_qrv(self, dxcallsign: bytes, snr) -> None:
        """
        Called when we send a QRV frame
        Args:
          self,
          dxcallsign

        """
        # Sleep a random amount of time before responding to make it more likely to be
        # heard when many stations respond. Each DATAC0 frame is 0.44 sec (440ms) in
        # duration, plus overhead. Set the wait interval to be random between 0 and
        # self.duration_sig1_frame * 4 == 4 slots
        # in self.duration_sig1_frame increments.
        # FIXME This causes problems when running ctests - we need to figure out why
        if not TESTMODE:
            self.log.info("[Modem] Waiting for QRV slot...")
            helpers.wait(randrange(0, int(self.duration_sig1_frame * 4), self.duration_sig1_frame * 10 // 10.0))

        send_data_to_socket_queue(
            freedata="modem-message",
            qrv="transmitting",
            dxcallsign=str(dxcallsign, "UTF-8"),
        )

        self.log.info("[Modem] Sending QRV!")
        print(self.mycallsign)
        qrv_frame = bytearray(self.length_sig0_frame)
        qrv_frame[:1] = bytes([FR_TYPE.QRV.value])
        qrv_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
        qrv_frame[7:11] = helpers.encode_grid(self.mygrid)
        qrv_frame[11:12] = helpers.snr_to_bytes(snr)

        if self.enable_fsk:
            self.log.info("[Modem] ENABLE FSK", state=self.enable_fsk)
            enqueue_frame_for_tx([qrv_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            enqueue_frame_for_tx([qrv_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

    def received_qrv(self, data_in: bytes, snr) -> None:
        """
        Called when we receive a QRV frame
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        self.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")
        dxsnr = helpers.snr_from_bytes(data_in[11:12])

        combined_snr = f"{snr}/{dxsnr}"

        send_data_to_socket_queue(
            freedata="modem-message",
            qrv="received",
            dxcallsign=str(dxcallsign, "UTF-8"),
            dxgrid=str(self.dxgrid, "UTF-8"),
            snr=str(snr),
            dxsnr=str(dxsnr)
        )

        self.log.info(
            "[Modem] QRV RCVD ["
            + str(dxcallsign, "UTF-8")
            + "]["
            + str(self.dxgrid, "UTF-8")
            + "] ",
            snr=snr,
            dxsnr=dxsnr
        )
        helpers.add_to_heard_stations(
            dxcallsign,
            self.dxgrid,
            "QRV",
            combined_snr,
            self.modem_frequency_offset,
            self.states.radio_frequency,
            self.states.heard_stations
        )



    def received_is_writing(self, data_in: bytes, snr) -> None:
        """
        Called when we receive a IS WRITING frame
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))

        send_data_to_socket_queue(
            freedata="modem-message",
            fec="is_writing",
            dxcallsign=str(dxcallsign, "UTF-8")
        )

        self.log.info(
            "[Modem] IS_WRITING RCVD ["
            + str(dxcallsign, "UTF-8")
            + "] ",
        )


# ----------- BROADCASTS
    def run_beacon(self) -> None:
        """
        Controlling function for running a beacon
        Args:

          self: arq class

        Returns:

        """
        try:
            while True:
                threading.Event().wait(0.5)
                while self.states.is_beacon_running:
                    if (
                            not self.states.is_arq_session
                            and not self.arq_file_transfer
                            and not self.beacon_paused
                            #and not self.states.channel_busy
                            and not self.states.is_modem_busy
                            and not self.states.is_arq_state
                    ):
                        send_data_to_socket_queue(
                            freedata="modem-message",
                            beacon="transmitting",
                            dxcallsign="None",
                            interval=self.beacon_interval,
                        )
                        self.log.info(
                            "[Modem] Sending beacon!", interval=self.beacon_interval
                        )

                        beacon_frame = bytearray(self.length_sig0_frame)
                        beacon_frame[:1] = bytes([FR_TYPE.BEACON.value])
                        beacon_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
                        beacon_frame[7:11] = helpers.encode_grid(self.mygrid)

                        if self.enable_fsk:
                            self.log.info("[Modem] ENABLE FSK", state=self.enable_fsk)
                            enqueue_frame_for_tx(
                                [beacon_frame],
                                c2_mode=FREEDV_MODE.fsk_ldpc_0.value,
                            )
                        else:
                            enqueue_frame_for_tx([beacon_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1,
                                                      repeat_delay=0)
                            if self.enable_morse_identifier:
                                MODEM_TRANSMIT_QUEUE.put(["morse", 1, 0, self.mycallsign])

                    self.beacon_interval_timer = time.time() + self.beacon_interval
                    while (
                            time.time() < self.beacon_interval_timer
                            and self.states.is_beacon_running
                            and not self.beacon_paused
                    ):
                        threading.Event().wait(0.01)

        except Exception as err:
            self.log.debug("[Modem] run_beacon: ", exception=err)

    def received_beacon(self, data_in: bytes, snr) -> None:
        """
        Called if we received a beacon
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        beacon_callsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        self.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")
        send_data_to_socket_queue(
            freedata="modem-message",
            beacon="received",
            uuid=str(uuid.uuid4()),
            timestamp=int(time.time()),
            dxcallsign=str(beacon_callsign, "UTF-8"),
            dxgrid=str(self.dxgrid, "UTF-8"),
            snr=str(snr),
        )

        self.log.info(
            "[Modem] BEACON RCVD ["
            + str(beacon_callsign, "UTF-8")
            + "]["
            + str(self.dxgrid, "UTF-8")
            + "] ",
            snr=snr,
        )
        helpers.add_to_heard_stations(
            beacon_callsign,
            self.dxgrid,
            "BEACON",
            snr,
            self.modem_frequency_offset,
            self.states.radio_frequency,
            self.states.heard_stations
        )