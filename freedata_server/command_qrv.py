from freedata_server.command import TxCommand


class QRVCommand(TxCommand):
    """Command for transmitting QRV frames.

    This command builds and transmits QRV (Ready to Receive) frames.
    """

    def set_params_from_api(self, apiParams):
        """Sets parameters from the API request.

        Extracts the SNR of the triggering frame (e.g. a received CQ), which
        is reported back in the QRV frame. Defaults to 0 if not provided.

        Args:
            apiParams (dict): A dictionary containing the API parameters.

        Returns:
            dict: The API parameters after processing.
        """
        self.snr = apiParams.get("snr", 0) if apiParams else 0
        if self.snr is None:
            self.snr = 0
        return super().set_params_from_api(apiParams)

    def build_frame(self):
        """Builds a QRV frame.

        This method uses the frame factory to build a QRV (Ready to Receive)
        frame.

        Returns:
            bytearray: The built QRV frame.
        """
        return self.frame_factory.build_qrv(self.snr)
