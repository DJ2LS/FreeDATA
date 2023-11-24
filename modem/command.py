from data_frame_factory import DataFrameFactory
from modem.modem import RF

class TxCommand():

    def __init__(self, apiParams):
        self.setParamsFromApi(apiParams)
        self.frame_factory = DataFrameFactory(modem)

    def setParamsFromApi(self, apiParams):
        pass

    def getName(self):
        return type(self).__name__

    def getPayload(self):
        pass
    
    def execute(self, modem_state, tx_frame_queue):
        pass

    def transmit(self, frame):
        # MODEM_TRANSMIT_QUEUE.put([c2_mode, copies, repeat_delay, frame_to_tx])

        self.modem.modem_transmit_queue.put(

        )
