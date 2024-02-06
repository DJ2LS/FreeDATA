from command import TxCommand
import api_validations
import base64
from queue import Queue
from arq_session_iss import ARQSessionISS
from message_p2p import MessageP2P
from arq_data_type_handler import ARQ_SESSION_TYPES
from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages

class SendMessageCommand(TxCommand):
    """Command to send a P2P message using an ARQ transfer session
    """

    def set_params_from_api(self, apiParams):
        print(apiParams)
        origin = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
        self.message = MessageP2P.from_api_params(origin, apiParams)
        print(self.message.id)
        print(self.message.to_dict())
        print("--------------------------------------- set params from api")
        DatabaseManagerMessages(self.event_manager).add_message(self.message.to_dict(), direction='transmit', status='queued')

    def transmit(self, modem):

        if self.state_manager.getARQ():
            self.log("Modem busy, waiting until ready...")
            return

        first_queued_message = DatabaseManagerMessages(self.event_manager).get_first_queued_message()
        if not first_queued_message:
            self.log("No queued message in database.")
            return

        self.log(f"Queued message found: {first_queued_message['id']}")
        DatabaseManagerMessages(self.event_manager).update_message(first_queued_message["id"], update_data={'status': 'transmitting'})
        message_dict = DatabaseManagerMessages(self.event_manager).get_message_by_id(first_queued_message["id"])
        print(message_dict["id"])
        message = MessageP2P.from_api_params(message_dict['origin'], message_dict)
        print(message.id)
        print("--------------------------------------- transmit")

        # Convert JSON string to bytes (using UTF-8 encoding)
        payload = message.to_payload().encode('utf-8')
        json_bytearray = bytearray(payload)
        data, data_type = self.arq_data_type_handler.prepare(json_bytearray, ARQ_SESSION_TYPES.p2pmsg_lzma)

        iss = ARQSessionISS(self.config,
                            modem,
                            self.message.destination,
                            self.state_manager,
                            data,
                            data_type
                            )
        
        self.state_manager.register_arq_iss_session(iss)
        iss.start()
