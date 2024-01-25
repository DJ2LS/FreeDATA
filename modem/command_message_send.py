from command import TxCommand
import api_validations
import base64
from queue import Queue
from arq_session_iss import ARQSessionISS
from message_p2p import MessageP2P
from arq_data_type_handler import ARQDataTypeHandler

class SendMessageCommand(TxCommand):
    """Command to send a P2P message using an ARQ transfer session
    """

    def set_params_from_api(self, apiParams):
        origin = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
        self.message = MessageP2P.from_api_params(origin, apiParams)

    def transmit(self, modem):
        # Convert JSON string to bytes (using UTF-8 encoding)
        payload = self.message.to_payload().encode('utf-8')
        json_bytearray = bytearray(payload)
        data, data_type = self.arq_data_type_handler.prepare(json_bytearray, 'p2pmsg_lzma')
        iss = ARQSessionISS(self.config,
                            modem,
                            self.message.destination,
                            self.state_manager,
                            data,
                            data_type
                            )
        
        self.state_manager.register_arq_iss_session(iss)
        iss.start()
