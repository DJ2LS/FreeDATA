import datetime
import api_validations
import base64
import json
from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
#import command_message_send


def message_received(event_manager, state_manager, data, statistics):
    decompressed_json_string = data.decode('utf-8')
    received_message_obj = MessageP2P.from_payload(decompressed_json_string)
    received_message_dict = MessageP2P.to_dict(received_message_obj)
    DatabaseManagerMessages(event_manager).add_message(received_message_dict, statistics, direction='receive', status='received', is_read=False)

def message_transmitted(event_manager, state_manager, data, statistics):
    decompressed_json_string = data.decode('utf-8')
    payload_message_obj = MessageP2P.from_payload(decompressed_json_string)
    payload_message = MessageP2P.to_dict(payload_message_obj)
    # Todo we need to optimize this - WIP
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'status': 'transmitted'})
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'statistics': statistics})


def message_failed(event_manager, state_manager, data, statistics):
    decompressed_json_string = data.decode('utf-8')
    payload_message_obj = MessageP2P.from_payload(decompressed_json_string)
    payload_message = MessageP2P.to_dict(payload_message_obj)
    # Todo we need to optimize this - WIP
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'status': 'failed'})
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'statistics': statistics})

class MessageP2P:
    def __init__(self, id: str, origin: str, destination: str, body: str, attachments: list) -> None:
        self.id = id
        self.timestamp = datetime.datetime.now().isoformat()
        self.origin = origin
        self.destination = destination
        self.body = body
        self.attachments = attachments

    @classmethod
    def from_api_params(cls, origin: str, params: dict):

        destination = params['destination']
        if not api_validations.validate_freedata_callsign(destination):
            destination = f"{destination}-0"

        if not api_validations.validate_freedata_callsign(destination):
            raise ValueError(f"Invalid destination given ({params['destination']})")

        body = params['body']

        attachments = []
        if 'attachments' in params: 
            for a in params['attachments']:
                api_validations.validate_message_attachment(a)
                attachments.append(cls.__decode_attachment__(a))

        timestamp = datetime.datetime.now().isoformat()
        if 'id' not in params:
            msg_id = f"{origin}_{destination}_{timestamp}"
        else:
            msg_id = params["id"]

        return cls(msg_id, origin, destination, body, attachments)
        
    @classmethod
    def from_payload(cls, payload):
        payload_message = json.loads(payload)
        attachments = list(map(cls.__decode_attachment__, payload_message['attachments']))
        return cls(payload_message['id'], payload_message['origin'], payload_message['destination'],
                   payload_message['body'], attachments)

    def get_id(self) -> str:
        return f"{self.origin}_{self.destination}_{self.timestamp}"

    def __encode_attachment__(self, binary_attachment: dict):
        encoded_attachment = binary_attachment.copy()
        encoded_attachment['data'] = str(base64.b64encode(binary_attachment['data']), 'utf-8')
        return encoded_attachment
    
    def __decode_attachment__(encoded_attachment: dict):
        decoded_attachment = encoded_attachment.copy()
        decoded_attachment['data'] = base64.b64decode(encoded_attachment['data'])
        return decoded_attachment

    def to_dict(self):
        """Make a dictionary out of the message data
        """

        return {
            'id': self.id,
            'origin': self.origin,
            'destination': self.destination,
            'body': self.body,
            'attachments': list(map(self.__encode_attachment__, self.attachments)),
        }
    
    def to_payload(self):
        """Make a byte array ready to be sent out of the message data"""
        json_string = json.dumps(self.to_dict())
        return json_string

