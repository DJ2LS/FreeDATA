import frame_handler
import helpers
import data_frame_factory

class PingFrameHandler(frame_handler.FrameHandler):

    #def is_frame_for_me(self):
    #    call_with_ssid = self.config['STATION']['mycall'] + "-" + str(self.config['STATION']['myssid'])
    #    valid, mycallsign = helpers.check_callsign(
    #        call_with_ssid,
    #        self.details["frame"]["destination_crc"],
    #        self.config['STATION']['ssid_list'])

    #    if not valid:
    #        ft = self.details['frame']['frame_type']
    #        self.logger.info(f"[Modem] {ft} received but not for us.")
    #    return valid

    def follow_protocol(self):
        if not bool(self.is_frame_for_me() and not self.states.getARQ()):
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