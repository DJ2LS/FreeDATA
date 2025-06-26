import threading
from modem_frametypes import FRAME_TYPE as FR

import frame_handler_ping
import helpers
import data_frame_factory
import frame_handler
from message_system_db_broadcasts import DatabaseManagerBroadcasts
import numpy as np

from norm.norm_transmission_irs import NormTransmissionIRS
from norm.norm_transmission_iss import NormTransmissionISS

class NORMFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):
        #self.logger.debug(f"[NORM] handling burst:{self.details}")

        #origin = self.details["frame"]["origin"]
        #print(origin)
        frame = self.details['frame']

        if frame['frame_type_int'] == FR.NORM_DATA.value:
            NormTransmissionIRS(self.ctx, frame)

        elif frame['frame_type_int'] == FR.NORM_REPAIR.value:
            NormTransmissionIRS(self.ctx, frame)

        elif frame['frame_type_int'] == FR.NORM_NACK.value:
            broadcast = DatabaseManagerBroadcasts(self.ctx).get_broadcast_per_id(frame["id"])
            if broadcast is not None:
                print(broadcast)
                NormTransmissionISS(self.ctx, broadcast.origin, broadcast.domain, broadcast.gridsquare, broadcast.data, priority=broadcast.priority, message_type=broadcast.message_type)
        else:
            self.logger.warning("DISCARDING FRAME", frame=frame)
            return
