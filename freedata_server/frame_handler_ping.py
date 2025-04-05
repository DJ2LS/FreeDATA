import frame_handler
import helpers
import data_frame_factory
from message_system_db_messages import DatabaseManagerMessages


class PingFrameHandler(frame_handler.FrameHandler):
    """Handles received PING frames.

    This class processes received PING frames, sends acknowledgements, and
    checks for queued messages to be sent based on configuration.
    """

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
        """Processes the received PING frame.

        This method checks if the frame is for the current station and if
        the modem is not busy with ARQ. If both conditions are met, it sends
        a PING acknowledgement and checks for queued messages to send.
        """
        if not bool(self.is_frame_for_me() and not self.states.getARQ()):
            return
        self.logger.debug(
            f"[Modem] Responding to request from [{self.details['frame']['origin']}]",
            snr=self.details['snr'],
        )
        self.send_ack()

        self.check_for_queued_message()

    def send_ack(self):
        """Sends a PING acknowledgement frame.

        This method builds a PING acknowledgement frame using the received
        frame's origin CRC and SNR, and transmits it using the modem.
        """
        factory = data_frame_factory.DataFrameFactory(self.config)
        ping_ack_frame = factory.build_ping_ack(
            self.details['frame']['origin_crc'], 
            self.details['snr']
        )
        self.transmit(ping_ack_frame)

    def check_for_queued_message(self):
        """Checks for queued messages to send.

        This method checks if auto-repeat is enabled in the configuration
        and if the received signal strength is above a certain threshold.
        If both conditions are met, it sets any messages addressed to the
        originating station to 'queued' status in the message database.
        """

        # only check for queued messages, if we have enabled this and if we have a minimum snr received
        if self.config["MESSAGES"]["enable_auto_repeat"] and self.details["snr"] >= -2:
            # set message to queued if beacon received
            DatabaseManagerMessages(self.event_manager).set_message_to_queued_for_callsign(
                self.details['frame']["origin"])