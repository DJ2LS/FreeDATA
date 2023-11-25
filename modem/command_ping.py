from command import TxCommand

class PingCommand(TxCommand):

    def setParamsFromApi(self, apiParams):
        self.dxcall = apiParams['dxcall']
        return super().setParamsFromApi()

    def build_frame(self):
        return self.frame_factory.build_ping(self.dxcall)
