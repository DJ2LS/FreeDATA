import frame_handler_ping
import helpers
import data_frame_factory

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
