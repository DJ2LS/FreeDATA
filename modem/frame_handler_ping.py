import frame_handler
import helpers
import data_frame_factory

class PingFrameHandler(frame_handler.FrameHandler):

    def make_event(self):
        event = super().make_event()
        event['ping'] = "received"
        return event

    def follow_protocol(self):
        deconstructed_frame = self.details['frame']
        origin = deconstructed_frame["origin"]

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(
            self.config['STATION']['mycall'], 
            deconstructed_frame["destination_crc"],
            self.config['STATION']['ssid_list'])

        if not valid:
            # PING packet not for me.
            self.logger.debug("[Modem] received_ping: ping not for this station.")
            return

        self.dxcallsign_crc = deconstructed_frame["origin_crc"]
        self.dxcallsign = origin
        self.logger.info(
            f"[Modem] PING REQ from [{origin}] to [{mycallsign}]",
            snr=self.details['snr'],
        )

        self.send_ack()

    def send_ack(self):
        factory = data_frame_factory.DataFrameFactory(self.config)
        ping_ack_frame = factory.build_ping_ack(
            self.details['frame']['origin_crc'], 
            self.details['snr']
        )
        self.transmit(ping_ack_frame)