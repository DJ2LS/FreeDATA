import queue
from command import TxCommand
import api_validations
import base64
from queue import Queue
from arq_session_iss import ARQSessionISS
class ARQRawCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.dxcall = apiParams['dxcall']
        if not api_validations.validate_freedata_callsign(self.dxcall):
            self.dxcall = f"{self.dxcall}-0"

        self.data = base64.b64decode(apiParams['data'])

    def run(self, event_queue: Queue, tx_frame_queue: Queue):
        self.emit_event(event_queue)
        self.logger.info(self.log_message())

        iss = ARQSessionISS(self.config, tx_frame_queue, self.dxcall, self.data)
        self.state_manager.register_arq_iss_session(iss)
        iss.run()
        return iss
