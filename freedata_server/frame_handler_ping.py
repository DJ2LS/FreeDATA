from freedata_server import frame_handler
from freedata_server import data_frame_factory


class PingFrameHandler(frame_handler.FrameHandler):
    """Handles received PING frames.

    This class processes received PING frames, sends acknowledgements, and
    checks for queued messages to be sent based on configuration.
    """

    # def is_frame_for_me(self):
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
        if not bool(self.is_frame_for_me() and not self.ctx.state_manager.getARQ()):
            return
        self.logger.debug(
            f"[Modem] Responding to request from [{self.details['frame']['origin']}]",
            snr=self.details["snr"],
        )
        self.send_ack()
        self.check_for_queued_message()

    def send_ack(self):
        """Sends a PING acknowledgement frame.

        This method builds a PING acknowledgement frame using the received
        frame's origin CRC and SNR, and transmits it using the modem.
        """
        factory = data_frame_factory.DataFrameFactory(self.ctx)
        ping_ack_frame = factory.build_ping_ack(
            self.details["frame"]["origin_crc"], self.details["snr"]
        )
        self.transmit(ping_ack_frame)
