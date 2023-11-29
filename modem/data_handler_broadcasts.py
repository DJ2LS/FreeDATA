import time
from modem_frametypes import FRAME_TYPE as FR_TYPE
from codec2 import FREEDV_MODE
from queues import MODEM_TRANSMIT_QUEUE
import helpers
from random import randrange
import uuid
import structlog
import event_manager
import command_qrv

from data_handler import DATA

TESTMODE = False

class BROADCAST(DATA):

    def __init__(self, config, event_queue, states):
        super().__init__(config, event_queue, states)

        self.log = structlog.get_logger("DHBC")
        self.states = states
        self.event_queue = event_queue
        self.config = config
        
        self.event_manager = event_manager.EventManager([event_queue])

        # length of signalling frame
        self.length_sig0_frame = 14
        self.modem_frequency_offset = 0

        # load config
        self.mycallsign = config['STATION']['mycall']
        self.myssid = config['STATION']['myssid']
        self.mycallsign += "-" + str(self.myssid)
        encoded_call = helpers.callsign_to_bytes(self.mycallsign)
        self.mycallsign_bytes = helpers.bytes_to_callsign(encoded_call)
        self.mygrid = config['STATION']['mygrid']
        self.enable_fsk = config['MODEM']['enable_fsk']
        self.respond_to_cq = config['MODEM']['respond_to_cq']
        self.respond_to_call = True

        self.duration_datac13 = 2.0
        self.duration_sig1_frame = self.duration_datac13

    def received_cq(self, frame_data, snr) -> None:
        """
        Called when we receive a CQ frame
        Args:
          data_in:bytes:

        Returns:
            Nothing
        """
        # here we add the received station to the heard stations buffer
        dxcallsign = frame_data['origin']
        self.log.debug("[Modem] received_cq:", dxcallsign=dxcallsign)
        self.dxgrid = frame_data['gridsquare']

        self.event_manager.send_custom_event(
            freedata="modem-message",
            cq="received",
            mycallsign=self.mycallsign,
            dxcallsign=dxcallsign,
            dxgrid=self.dxgrid,
        )

        self.log.info(
            "[Modem] CQ RCVD ["
            + dxcallsign
            + "]["
            + self.dxgrid
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

        # Sleep a random amount of time before responding to make it more likely to be
        # heard when many stations respond. Each DATAC0 frame is 0.44 sec (440ms) in
        # duration, plus overhead. Set the wait interval to be random between 0 and
        # self.duration_sig1_frame * 4 == 4 slots
        # in self.duration_sig1_frame increments.
        if self.respond_to_cq and self.respond_to_call:
            params = {'snr': snr, 'dxcall': dxcallsign}
            cmd = command_qrv.QRVCommand(self.config, self.log, params)
            cmd.run(self.event_queue, MODEM_TRANSMIT_QUEUE)

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

        self.event_manager.send_custom_event(
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

        self.event_manager.send_custom_event(
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
    def received_beacon(self, frame_data, snr) -> None:
        """
        Called if we received a beacon
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        beacon_callsign = frame_data['origin']
        self.dxgrid = frame_data['gridsquare']

        self.event_manager.send_custom_event(
            freedata="modem-message",
            beacon="received",
            uuid=str(uuid.uuid4()),
            timestamp=int(time.time()),
            dxcallsign=beacon_callsign,
            dxgrid=self.dxgrid,
            snr=str(snr),
        )

        self.log.info(
            f"[Modem] BEACON RCVD [{beacon_callsign}][{self.dxgrid}]",
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
