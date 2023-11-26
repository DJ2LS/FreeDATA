from command import TxCommand

class BeaconCommand(TxCommand):

    def build_frame(self):
        return self.frame_factory.build_beacon()

    def transmit(self, tx_frame_queue):
        super().transmit(tx_frame_queue)
        if self.config['MODEM']['enable_morse_identifier']:
            mycall = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
            tx_frame_queue.put(["morse", 1, 0, mycall])
