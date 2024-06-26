import threading

import frame_handler_ping
import helpers
import data_frame_factory
import frame_handler
from message_system_db_messages import DatabaseManagerMessages
import numpy as np

class CQFrameHandler(frame_handler.FrameHandler):

    #def should_respond(self):
    #    self.logger.debug(f"Respond to CQ: {self.config['MODEM']['respond_to_cq']}")
    #    return bool(self.config['MODEM']['respond_to_cq'] and not self.states.getARQ())

    def follow_protocol(self):

        if self.states.getARQ():
            return

        self.logger.debug(
            f"[Modem] Responding to request from [{self.details['frame']['origin']}]",
            snr=self.details['snr'],
        )

        self.send_ack()

    def send_ack(self):
        factory = data_frame_factory.DataFrameFactory(self.config)
        qrv_frame = factory.build_qrv(self.details['snr'])

        # wait some random time and wait if we have an ongoing codec2 transmission
        # on our channel. This should prevent some packet collision
        random_delay = np.random.randint(0, 6)
        threading.Event().wait(random_delay)
        self.states.channel_busy_condition_codec2.wait(5)

        self.transmit(qrv_frame)

        if self.config["MESSAGES"]["enable_auto_repeat"]:
            # set message to queued if CQ received
            DatabaseManagerMessages(self.event_manager).set_message_to_queued_for_callsign(self.details['frame']["origin"])
