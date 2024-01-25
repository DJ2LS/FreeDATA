import datetime
import api_validations
import base64
import json


class MessageP2P:
    def __init__(self, origin: str, destination: str, body: str, attachments: list) -> None:
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

        return cls(origin, dxcall, body, attachments)
        
    @classmethod
    def from_payload(cls, payload):
        payload_message = json.loads(payload)
        attachments = list(map(cls.__decode_attachment__, payload_message['attachments']))
        return cls(payload_message['origin'], payload_message['destination'], 
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

    def to_dict(self, received=False):
        """Make a dictionary out of the message data
        """

        if received:
            direction = 'receive'
        else:
            direction = 'transmit'

        return {
            'id': self.get_id(),
            'origin': self.origin,
            'destination': self.destination,
            'body': self.body,
            'direction': direction,
            'attachments': list(map(self.__encode_attachment__, self.attachments)),
        }
    
    def to_payload(self):
        """Make a byte array ready to be sent out of the message data"""
        json_string = json.dumps(self.to_dict())
        return json_string
