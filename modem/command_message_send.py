from command import TxCommand
import api_validations
import base64
from queue import Queue
from arq_session_iss import ARQSessionISS
from message_p2p import MessageP2P

class SendMessageCommand(TxCommand):
    """Command to send a P2P message using an ARQ transfer session
    """

    def set_params_from_api(self, apiParams):
        origin = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
        self.message = MessageP2P.from_api_params(origin, apiParams)

    def transmit(self, modem):
        iss = ARQSessionISS(self.config, modem, 
                            self.message.destination, 
                            self.message.to_payload(), 
                            self.state_manager)
        
        self.state_manager.register_arq_iss_session(iss)
        iss.start()
