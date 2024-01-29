import datetime
import api_validations
import base64
import json
from message_system_db_manager import DatabaseManager


def message_received(event_manager, data):
    decompressed_json_string = data.decode('utf-8')
    received_message_obj = MessageP2P.from_payload(decompressed_json_string)
    received_message_dict = MessageP2P.to_dict(received_message_obj)
    DatabaseManager(event_manager).add_message(received_message_dict, direction='receive', status='received')

def message_failed(event_manager, data):
    decompressed_json_string = data.decode('utf-8')
    payload_message = json.loads(decompressed_json_string)
    DatabaseManager(event_manager).update_message(payload_message["id"], update_data={'status' : 'failed'})


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

        dxcall = params['dxcall']
        if not api_validations.validate_freedata_callsign(dxcall):
            dxcall = f"{dxcall}-0"

        if not api_validations.validate_freedata_callsign(dxcall):
            raise ValueError(f"Invalid dxcall given ({params['dxcall']})")

        body = params['body']
        if len(body) < 1:
            raise ValueError(f"Body cannot be empty")

        attachments = []
        if 'attachments' in params: 
            for a in params['attachments']:
                api_validations.validate_message_attachment(a)
                attachments.append(cls.__decode_attachment__(a))

        timestamp = datetime.datetime.now().isoformat()
        msg_id = f"{origin}_{dxcall}_{timestamp}"

        return cls(msg_id, origin, dxcall, body, attachments)
        
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

