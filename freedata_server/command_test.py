from command import TxCommand
import codec2
from codec2 import FREEDV_MODE


class TestCommand(TxCommand):
    """Command for transmitting test frames.

    This command builds and transmits test frames using a specific FreeDV
    mode (data_ofdm_500).
    """

    def build_frame(self):
        """Builds a test frame.

        This method uses the frame factory to build a test frame using the
        specified FreeDV mode.

        Returns:
            bytearray: The built test frame.
        """
        return self.frame_factory.build_test(self.get_tx_mode().name)

    def get_tx_mode(self):
        """Returns the transmission mode for test frames.

        This method returns the specific FreeDV mode (data_ofdm_500) used for
        transmitting test frames.

        Returns:
            codec2.FREEDV_MODE: The FreeDV mode for test frames.
        """
        if self.config['EXP'].get('enable_vhf'):
            mode = FREEDV_MODE.data_vhf_1
        else:
            mode = FREEDV_MODE.data_ofdm_500

        return mode
