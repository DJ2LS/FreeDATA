from command import TxCommand
from codec2 import FREEDV_MODE
class CQCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_cq()
