from command import TxCommand

class TransmitSine(TxCommand):
    def transmit(self, modem):
        #modem.transmit_sine()
        modem.transmit_morse(0,0,[b''])