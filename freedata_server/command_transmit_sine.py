from command import TxCommand

class TransmitSine(TxCommand):
    """Command for transmitting a sine wave.

    This command instructs the modem to transmit a continuous sine wave,
    which can be used for testing and calibration.
    """
    def transmit(self, modem):
        """Transmits a sine wave.

        This method instructs the modem to transmit a sine wave.  It is used
        for testing and calibration purposes.

        Args:
            modem: The modem object.
        """
        modem.transmit_sine()
        # Code for debugging morse stuff...
        #modem.transmit_morse(0,0,[b''])