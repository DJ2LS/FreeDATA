from command import TxCommand

class TransmitSine(TxCommand):
    def transmit(self, modem):
        modem.transmit_sine()