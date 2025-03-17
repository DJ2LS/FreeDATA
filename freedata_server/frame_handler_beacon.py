import frame_handler
import datetime
from message_system_db_beacon import DatabaseManagerBeacon
from message_system_db_messages import DatabaseManagerMessages


from message_system_db_manager import DatabaseManager
class BeaconFrameHandler(frame_handler.FrameHandler):
    """Handles received beacon frames.

    This class processes received beacon frames, stores them in the database,
    and checks for queued messages to be sent based on configuration and
    signal strength.
    """

    def follow_protocol(self):
        """Processes the received beacon frame.

        This method adds the beacon information to the database and checks
        for queued messages to send if auto-repeat is enabled and the
        signal strength is above a certain threshold.
        """
        DatabaseManagerBeacon(self.event_manager).add_beacon(datetime.datetime.now(),
                                                             self.details['frame']["origin"],
                                                             self.details["snr"],
                                                             self.details['frame']["gridsquare"]
                                                             )

        # only check for queued messages, if we have enabled this and if we have a minimum snr received
        if self.config["MESSAGES"]["enable_auto_repeat"] and self.details["snr"] >= -2:
            # set message to queued if beacon received
            DatabaseManagerMessages(self.event_manager).set_message_to_queued_for_callsign(self.details['frame']["origin"])
