import frame_handler_ping
import helpers
import data_frame_factory
import frame_handler
import datetime
from message_system_db_beacon import DatabaseManagerBeacon


from message_system_db_manager import DatabaseManager
class BeaconFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):
        DatabaseManagerBeacon(self.event_manager).add_beacon(datetime.datetime.now(),
                                                             self.details['frame']["origin"],
                                                             self.details["snr"],
                                                             self.details['frame']["gridsquare"]
                                                             )
