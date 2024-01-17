from command import TxCommand

class CQCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_cq()
