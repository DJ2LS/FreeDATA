from command import TxCommand

class QRVCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_qrv()
