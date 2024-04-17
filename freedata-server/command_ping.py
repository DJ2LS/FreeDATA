from command import TxCommand
import api_validations
from message_system_db_manager import DatabaseManager


class PingCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.dxcall = apiParams['dxcall']
        if not api_validations.validate_freedata_callsign(self.dxcall):
            self.dxcall = f"{self.dxcall}-0"

        # update callsign database...
        DatabaseManager(self.event_manager).get_or_create_station(self.dxcall)

        return super().set_params_from_api(apiParams)

    def build_frame(self):
        return self.frame_factory.build_ping(self.dxcall)
