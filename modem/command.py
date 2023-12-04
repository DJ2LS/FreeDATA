from data_frame_factory import DataFrameFactory
import queue
from codec2 import FREEDV_MODE
import structlog

class TxCommand():

    def __init__(self, config, state_manager, modem_events, apiParams = {}):
        self.config = config
        self.logger = structlog.get_logger("Command")
        self.state_manager = state_manager
        self.modem_events = modem_events
        self.set_params_from_api(apiParams)
        self.frame_factory = DataFrameFactory(config)

    def set_params_from_api(self, apiParams):
        pass

    def get_name(self):
        return type(self).__name__

    def emit_event(self, event_queue):
        pass

    def log_message(self):
        return f"Running {self.get_name()}"

    def build_frame(self):
        pass

    def get_tx_mode(self):
        return (
            FREEDV_MODE.fsk_ldpc_0.value
            if self.config['MODEM']['enable_fsk']
            else FREEDV_MODE.sig0.value
        )
    
    def make_modem_queue_item(self, mode, repeat, repeat_delay, frame):
        return {
            'mode': mode,
            'repeat': repeat,
            'repeat_delay': repeat_delay,
            'frame': frame,
        }

    def transmit(self, tx_frame_queue):
        frame = self.build_frame()
        tx_queue_item = self.make_modem_queue_item(self.get_tx_mode(), 1, 0, frame)
        tx_frame_queue.put(tx_queue_item)

    def run(self, event_queue: queue.Queue, tx_frame_queue: queue.Queue):
        self.emit_event(event_queue)
        self.logger.info(self.log_message())
        self.transmit(tx_frame_queue)
