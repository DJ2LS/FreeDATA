from command import TxCommand

class PingCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.dxcall = apiParams['dxcall']
        return super().set_params_from_api(apiParams)

    def build_frame(self):
        return self.frame_factory.build_ping(self.dxcall)
