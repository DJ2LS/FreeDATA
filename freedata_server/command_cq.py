from command import TxCommand
from codec2 import FREEDV_MODE
import modem
class CQCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_cq()

    def transmit(self, modem):
        modem.transmit_mfsk(b"test!")
        #modem.transmit_morse(1, 0, "test")