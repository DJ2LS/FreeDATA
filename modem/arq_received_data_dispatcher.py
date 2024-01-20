# File: arq_received_data_dispatcher.py

import structlog
from arq_data_formatter import ARQDataFormatter

class ARQReceivedDataDispatcher:
    def __init__(self):
        self.logger = structlog.get_logger(type(self).__name__)
        self.arq_data_formatter = ARQDataFormatter()
        self.endpoints = {
            "p2pmsg": self.handle_p2pmsg,
            "test": self.handle_test,
        }

    def log(self, message, isWarning=False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def dispatch(self, byte_data):
        """Use the data formatter to decapsulate and then dispatch data to the appropriate endpoint."""
        type_key, data = self.arq_data_formatter.decapsulate(byte_data)
        if type_key in self.endpoints:
            self.endpoints[type_key](data)
        else:
            self.handle_raw(data)

    def handle_p2pmsg(self, data):
        self.log(f"Handling p2pmsg: {data}")

    def handle_raw(self, data):
        self.log(f"Handling raw data: {data}")

    def handle_test(self, data):
        self.log(f"Handling test data: {data}")
