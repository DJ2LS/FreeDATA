import queue
from command import TxCommand
import api_validations
import base64
from queue import Queue
import numpy as np
import threading
from norm.norm_transmission_iss import NormTransmissionISS

class Norm(TxCommand):
    def set_params_from_api(self, apiParams):
        self.origin = apiParams['origin']
        if not api_validations.validate_freedata_callsign(self.origin):
            self.origin = f"{self.origin}-0"

        self.domain = apiParams['domain']
        if not api_validations.validate_freedata_callsign(self.domain):
            self.domain = f"{self.domain}-0"

        self.data = base64.b64decode(apiParams['data'])

        if 'priority' not in apiParams:
            self.priority = 1
        else:
            self.priority = apiParams['priority']

        self.msgtype = apiParams['type']
        self.gridsquare = apiParams['gridsquare']


    def run(self):
        try:
            self.emit_event()
            self.logger.info(self.log_message())

            NormTransmissionISS(self.ctx, self.origin, self.domain, self.gridsquare, self.data, self.priority, self.msgtype).prepare_and_transmit()





        except Exception as e:
            self.log(f"Error starting NORM transmission: {e}", isWarning=True)

        return False