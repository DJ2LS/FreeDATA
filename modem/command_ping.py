from command import TxCommand

class PingCommand(TxCommand):

    def setParamsFromApi(self, apiParams):
        self.dxcall = apiParams['dxcall']
        return super().setParamsFromApi()

    def run(self, modem_state, tx_frame_queue):
        frame = self.frame_factory.build_ping(self.dxcall)
        

        return super().execute(modem_state, tx_frame_queue)


