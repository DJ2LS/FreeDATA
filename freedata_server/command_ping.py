from command import TxCommand
import api_validations
from message_system_db_manager import DatabaseManager


class PingCommand(TxCommand):
    """Command for transmitting ping frames.

    This command sends a ping frame to a specified station, identified by
    its callsign. It also updates the callsign database.
    """

    def set_params_from_api(self, apiParams):
        """Sets parameters from the API request.

        This method extracts the destination callsign (dxcall) from the API
        parameters, validates it, adds a default SSID if needed, and updates
        the callsign database.

        Args:
            apiParams (dict): A dictionary containing the API parameters.

        Returns:
            dict: The API parameters after processing.
        """
        self.dxcall = apiParams['dxcall']
        if not api_validations.validate_freedata_callsign(self.dxcall):
            self.dxcall = f"{self.dxcall}-0"

        # update callsign database...
        DatabaseManager(self.event_manager).get_or_create_station(self.dxcall)

        return super().set_params_from_api(apiParams)

    def build_frame(self):
        """Builds a ping frame.

        This method uses the frame factory to build a ping frame addressed
        to the specified destination callsign.

        Returns:
            bytearray: The built ping frame.
        """
        return self.frame_factory.build_ping(self.dxcall)
