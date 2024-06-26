import queue
from command import TxCommand
import api_validations
import base64
from queue import Queue
from arq_session_iss import ARQSessionISS
from arq_data_type_handler import ARQ_SESSION_TYPES
import numpy as np
import threading

class ARQRawCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.dxcall = apiParams['dxcall']
        if not api_validations.validate_freedata_callsign(self.dxcall):
            self.dxcall = f"{self.dxcall}-0"

        try:
            self.type = ARQ_SESSION_TYPES[apiParams['type']]
        except KeyError:
            self.type = ARQ_SESSION_TYPES.raw

        self.data = base64.b64decode(apiParams['data'])

    def run(self, event_queue: Queue, modem):
        try:
            self.emit_event(event_queue)
            self.logger.info(self.log_message())

            # wait some random time and wait if we have an ongoing codec2 transmission
            # on our channel. This should prevent some packet collision
            random_delay = np.random.randint(0, 6)
            threading.Event().wait(random_delay)
            self.state_manager.channel_busy_condition_codec2.wait(5)

            prepared_data, type_byte = self.arq_data_type_handler.prepare(self.data, self.type)

            iss = ARQSessionISS(self.config, modem, self.dxcall, self.state_manager, prepared_data, type_byte)
            if iss.id:
                self.state_manager.register_arq_iss_session(iss)
                iss.start()
                return iss
        except Exception as e:
            self.log(f"Error starting ARQ session: {e}", isWarning=True)

        return False