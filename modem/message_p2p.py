import datetime
import api_validations
import base64
import json
import lzma


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
                attachments.append({
                    'name': a['name'],
                    'type': a['type'],
                    'data': base64.decode(a['data']),
                })

        return cls(origin, dxcall, body, attachments)
        
    def get_id(self) -> str:
        return f"{self.origin}.{self.destination}.{self.timestamp}"
    
    def to_dict(self):
        """Make a dictionary out of the message data
        """
        message = {
            'id': self.get_id(),
            'origin': self.origin,
            'destination': self.destination,
            'body': self.body,
            'attachments': self.attachments,
        }
        return message
    
    def to_payload(self):
        """Make a byte array ready to be sent out of the message data"""
        json_string = json.dumps(self.to_dict())
        json_bytes = bytes(json_string, 'utf-8')
        final_payload = lzma.compress(json_bytes)
        return final_payload
