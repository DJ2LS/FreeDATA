import frame_handler
import helpers
import data_frame_factory
from message_system_db_messages import DatabaseManagerMessages


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

        self.check_for_queued_message()

    def send_ack(self):
        factory = data_frame_factory.DataFrameFactory(self.config)
        ping_ack_frame = factory.build_ping_ack(
            self.details['frame']['origin_crc'], 
            self.details['snr']
        )
        self.transmit(ping_ack_frame)

    def check_for_queued_message(self):

        # only check for queued messages, if we have enabled this and if we have a minimum snr received
        if self.config["MESSAGES"]["enable_auto_repeat"] and self.details["snr"] >= -2:
            # set message to queued if beacon received
            DatabaseManagerMessages(self.event_manager).set_message_to_queued_for_callsign(
                self.details['frame']["origin"])