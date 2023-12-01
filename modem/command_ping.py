from command import TxCommand
import api_validations

class PingCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.dxcall = apiParams['dxcall']
        if not api_validations.validate_freedata_callsign(self.dxcall):
            self.dxcall = f"{self.dxcall}-0"

        return super().set_params_from_api(apiParams)

    def build_frame(self):
        return self.frame_factory.build_ping(self.dxcall)
