import frame_handler
import helpers
import data_frame_factory

class PingFrameHandler(frame_handler.FrameHandler):

    def is_frame_for_me(self):
        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(
            self.config['STATION']['mycall'], 
            self.details["frame"]["destination_crc"],
            self.config['STATION']['ssid_list'])

        if not valid:
            ft = self.details['frame']['frame_type']
            self.logger.info(f"[Modem] {ft} received but not for us.")

        return valid
    
    def should_respond(self):
        return self.is_frame_for_me()

    def follow_protocol(self):

        if not self.should_respond():
            return

        self.logger.debug(
            f"[Modem] Responding to request from [{self.details['frame']['origin']}]",
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