from command import TxCommand

class QRVCommand(TxCommand):
    """Command for transmitting QRV frames.

    This command builds and transmits QRV (Ready to Receive) frames.
    """

    def build_frame(self):
        """Builds a QRV frame.

        This method uses the frame factory to build a QRV (Ready to Receive)
        frame.

        Returns:
            bytearray: The built QRV frame.
        """
        return self.frame_factory.build_qrv()
