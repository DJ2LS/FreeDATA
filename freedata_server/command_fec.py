from command import TxCommand
import base64

class FecCommand(TxCommand):
    """Command for transmitting data using Forward Error Correction (FEC).

    This command prepares and transmits data packets using FEC, optionally
    sending a wakeup frame beforehand. It supports base64-encoded payloads
    and handles various FEC modes.
    """

    def set_params_from_api(self, apiParams):
        """Sets parameters from the API request.

        This method extracts the FEC mode, wakeup flag, and base64-encoded
        payload from the API parameters. It decodes the payload and raises
        a TypeError if the payload is not a valid base64 string.

        Args:
            apiParams (dict): A dictionary containing the API parameters.

        Raises:
            TypeError: If the payload is not a valid base64 string.

        Returns:
            dict: The API parameters after processing.
        """
        self.mode = apiParams['mode']
        self.wakeup = apiParams['wakeup']
        payload_b64 = apiParams['payload']

        if len(payload_b64) % 4:
            raise TypeError("Invalid base64 payload")
        self.payload = base64.b64decode(payload_b64)

        return super().set_params_from_api(apiParams)
    
    def build_wakeup_frame(self):
        """Builds a wakeup frame for FEC.

        This method uses the frame factory to build a wakeup frame for the
        specified FEC mode.

        Returns:
            bytearray: The built wakeup frame.
        """
        return self.frame_factory.build_fec_wakeup(self.mode)

    def build_frame(self):
        """Builds the FEC frame.

        This method uses the frame factory to build the FEC frame with the
        specified mode and payload.

        Returns:
            bytearray: The built FEC frame.
        """
        return self.frame_factory.build_fec(self. mode, self.payload)
    
    def transmit(self, tx_frame_queue):
        """Transmits the FEC frame, optionally sending a wakeup frame first.

        This method transmits the built FEC frame via the provided queue.
        If the wakeup flag is set, it sends a wakeup frame before the
        actual data frame.

        Args:
            tx_frame_queue: The transmission queue.
        """
        if self.wakeup:
            tx_queue_item = self.make_modem_queue_item(self.get_c2_mode(), 1, 0, self.build_wakeup_frame())
            tx_frame_queue.put(tx_queue_item)

        tx_queue_item = self.make_modem_queue_item(self.get_c2_mode(), 1, 0, self.build_frame())
        tx_frame_queue.put(tx_queue_item)
