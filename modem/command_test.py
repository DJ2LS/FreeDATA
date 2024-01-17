from command import TxCommand
import codec2

class TestCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_test()

    def get_tx_mode(self):
        return codec2.FREEDV_MODE.datac3