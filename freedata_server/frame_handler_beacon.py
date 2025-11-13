from freedata_server import frame_handler
import datetime
from freedata_server.message_system_db_beacon import DatabaseManagerBeacon
from freedata_server.message_system_db_messages import DatabaseManagerMessages


from freedata_server.message_system_db_manager import DatabaseManager


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
        DatabaseManagerBeacon(self.ctx).add_beacon(
            datetime.datetime.now(),
            self.details["frame"]["origin"],
            self.details["snr"],
            self.details["frame"]["gridsquare"],
        )

        self.check_for_queued_message()
