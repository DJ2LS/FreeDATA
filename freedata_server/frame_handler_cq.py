import threading

import frame_handler_ping
import helpers
import data_frame_factory
import frame_handler
from message_system_db_messages import DatabaseManagerMessages
import numpy as np

class CQFrameHandler(frame_handler.FrameHandler):
    """Handles received CQ frames.

    This class processes received CQ (Calling Any Station) frames and sends
    a QRV (Ready to Receive) frame as an acknowledgement if the station is
    not currently busy with ARQ. It also checks for queued messages to be
    sent based on the configuration.
    """

    #def should_respond(self):
    #    self.logger.debug(f"Respond to CQ: {self.ctx.config_manager.config['MODEM']['respond_to_cq']}")
    #    return bool(self.ctx.config_manager.config['MODEM']['respond_to_cq'] and not self.ctx.state_manager.getARQ())

    def follow_protocol(self):
        """Processes the received CQ frame.

        This method checks if the modem is currently busy with ARQ. If not,
        it sends a QRV frame as an acknowledgement and checks for queued
        messages to send.
        """

        if self.ctx.state_manager.getARQ():
            return

        self.logger.debug(
            f"[Modem] Responding to request from [{self.details['frame']['origin']}]",
            snr=self.details['snr'],
        )

        self.send_ack()
        self.check_for_queued_message()

    def send_ack(self):
        factory = data_frame_factory.DataFrameFactory(self.ctx)
        qrv_frame = factory.build_qrv(self.details['snr'])

        # wait some random time and wait if we have an ongoing codec2 transmission
        # on our channel. This should prevent some packet collision
        random_delay = np.random.randint(0, 6)
        threading.Event().wait(random_delay)
        self.ctx.state_manager.channel_busy_condition_codec2.wait(5)

        self.transmit(qrv_frame)

