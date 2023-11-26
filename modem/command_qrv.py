from command import TxCommand

class QRVCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        return super().set_params_from_api(apiParams)

    def build_frame(self):
        return self.frame_factory.build_qrv()
