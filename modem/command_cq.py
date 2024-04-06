from command import TxCommand
from codec2 import FREEDV_MODE
class CQCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_cq()

    def get_tx_mode(self):
        return FREEDV_MODE.data_ofdm_500
        #return FREEDV_MODE.datac3
        #return FREEDV_MODE.data_ofdm_2438
        #return FREEDV_MODE.qam16c2