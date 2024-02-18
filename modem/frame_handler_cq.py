import frame_handler_ping
import helpers
import data_frame_factory
import frame_handler
from message_system_db_messages import DatabaseManagerMessages


class CQFrameHandler(frame_handler_ping.PingFrameHandler):

    def should_respond(self):
        self.logger.debug(f"Respond to CQ: {self.config['MODEM']['respond_to_cq']}")
        return self.config['MODEM']['respond_to_cq']

    def send_ack(self):
        factory = data_frame_factory.DataFrameFactory(self.config)
        qrv_frame = factory.build_qrv(
            self.details['snr']
        )
        self.transmit(qrv_frame)

        if self.config["MESSAGES"]["enable_auto_repeat"]:
            # set message to queued if beacon received
            DatabaseManagerMessages(self.event_manager).set_message_to_queued_for_callsign(self.details['frame']["origin"])
