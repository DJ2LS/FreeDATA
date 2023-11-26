from command import TxCommand

class BeaconCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.enable_morse = apiParams['enable_morse']
        return super().set_params_from_api(apiParams)

    def build_frame(self):
        return self.frame_factory.build_beacon()

    def transmit(self, tx_frame_queue):
        super().transmit(tx_frame_queue)
        if self.enable_morse:
            mycall = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
            tx_frame_queue.put(["morse", 1, 0, mycall])
