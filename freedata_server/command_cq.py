from command import TxCommand
from codec2 import FREEDV_MODE
class CQCommand(TxCommand):
    """Command for transmitting CQ frames.

    This command builds and transmits CQ (Calling Any Station) frames using
    the FreeDV protocol.
    """

    def build_frame(self):
        """Builds a CQ frame.

        This method uses the frame factory to build a CQ (Calling Any Station)
        frame.

        Returns:
            bytearray: The built CQ frame.
        """
        return self.frame_factory.build_cq()
