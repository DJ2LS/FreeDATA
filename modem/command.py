from data_frame_factory import DataFrameFactory
from modem.modem import RF

class TxCommand():

    def __init__(self, modem: RF, apiParams):
        self.setParamsFromApi(apiParams)
        self.modem = modem
        self.frame_factory = DataFrameFactory(modem)

    def setParamsFromApi(self, apiParams):
        pass

    def getPayload(self):
        pass
    
    def execute(self, modem):
        pass

    def transmit(self, frame):
        # MODEM_TRANSMIT_QUEUE.put([c2_mode, copies, repeat_delay, frame_to_tx])

        self.modem.modem_transmit_queue.put(

        )
