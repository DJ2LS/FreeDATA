import threading

import frame_handler_ping
import helpers
import data_frame_factory
import frame_handler
from message_system_db_messages import DatabaseManagerMessages
import numpy as np

from norm.norm_transmission_irs import NormTransmissionIRS


class NORMFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):
        #self.logger.debug(f"[NORM] handling burst:{self.details}")

        #origin = self.details["frame"]["origin"]
        #print(origin)


        NormTransmissionIRS(self.ctx, self.details["frame"])