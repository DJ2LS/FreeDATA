from command import TxCommand

class BeaconCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_beacon()


    #def transmit(self, modem):
    #    super().transmit(modem)
    #    if self.config['MODEM']['enable_morse_identifier']:
    #        mycall = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
    #        modem.transmit_morse("morse", 1, 0, mycall)
