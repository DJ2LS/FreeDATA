from datetime import datetime, timezone
import api_validations
import base64
import json
from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
#import command_message_send


def message_received(event_manager, state_manager, data, statistics):
    """Handles a received P2P message.

    This function processes a received P2P message by decoding the data,
    converting it to a dictionary, and adding it to the message database.

    Args:
        event_manager (EventManager): The event manager instance.
        state_manager (StateManager): The state manager instance.
        data (bytes): The received message data.
        statistics (dict): Statistics about the message transmission.
    """
    decompressed_json_string = data.decode('utf-8')
    received_message_obj = MessageP2P.from_payload(decompressed_json_string)
    received_message_dict = MessageP2P.to_dict(received_message_obj)
    DatabaseManagerMessages(event_manager).add_message(received_message_dict, statistics, direction='receive', status='received', is_read=False, frequency=state_manager.radio_frequency)

def message_transmitted(event_manager, state_manager, data, statistics):
    """Handles a transmitted P2P message.

    This function processes a transmitted P2P message by decoding the
    data, converting it to a dictionary, and updating the message status
    and statistics in the database.

    Args:
        event_manager (EventManager): The event manager instance.
        state_manager (StateManager): The state manager instance.
        data (bytes): The transmitted message data.
        statistics (dict): Statistics about the message transmission.
    """
    decompressed_json_string = data.decode('utf-8')
    payload_message_obj = MessageP2P.from_payload(decompressed_json_string)
    payload_message = MessageP2P.to_dict(payload_message_obj)
    # Todo we need to optimize this - WIP
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'status': 'transmitted'})
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'statistics': statistics}, frequency=state_manager.radio_frequency)


def message_failed(event_manager, state_manager, data, statistics):
    """Handles a failed P2P message transmission.

    This function processes a failed P2P message transmission by decoding
    the data, converting it to a dictionary, and updating the message
    status and statistics in the database.

    Args:
        event_manager (EventManager): The event manager instance.
        state_manager (StateManager): The state manager instance.
        data (bytes): The message data that failed to transmit.
        statistics (dict): Statistics related to the failed transmission.
    """
    decompressed_json_string = data.decode('utf-8')
    payload_message_obj = MessageP2P.from_payload(decompressed_json_string)
    payload_message = MessageP2P.to_dict(payload_message_obj)
    # Todo we need to optimize this - WIP
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'status': 'failed'})
    DatabaseManagerMessages(event_manager).update_message(payload_message["id"], update_data={'statistics': statistics}, frequency=state_manager.radio_frequency)

class MessageP2P:
    """Represents a P2P message.

    This class encapsulates a peer-to-peer (P2P) message, including its ID,
    timestamp, origin, destination, message body, and attachments. It
    provides methods for creating messages from API parameters or payloads,
    encoding and decoding attachments, converting messages to dictionaries
    or payloads, and generating unique message IDs.
    """
    def __init__(self, id: str, origin: str, destination: str, body: str, attachments: list) -> None:
        """Initializes a new MessageP2P instance.

        Args:
            id (str): The unique ID of the message.
            origin (str): The callsign of the originating station.
            destination (str): The callsign of the destination station.
            body (str): The message body text.
            attachments (list): A list of attachments, where each attachment
                is a dictionary with 'name', 'data', and 'mime_type' keys.
        """
        self.id = id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.origin = origin
        self.destination = destination
        self.body = body
        self.attachments = attachments

    @classmethod
    def from_api_params(cls, origin: str, params: dict):
        """Creates a MessageP2P object from API parameters.

        This method creates a new P2P message object from the given API
        parameters, including origin, destination, message body, and
        attachments. It validates the destination callsign and attachments,
        decodes attachments, generates a message ID if not provided, and
        returns a new MessageP2P instance.

        Args:
            origin (str): The callsign of the originating station.
            params (dict): A dictionary containing the message parameters
                ('destination', 'body', and optionally 'attachments' and 'id').

        Raises:
            ValueError: If the destination callsign is invalid.

        Returns:
            MessageP2P: A new MessageP2P object.
        """

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

        timestamp = datetime.now(timezone.utc).isoformat()
        if 'id' not in params:
            msg_id = f"{origin}_{destination}_{timestamp}"
        else:
            msg_id = params["id"]

        return cls(msg_id, origin, destination, body, attachments)
        
    @classmethod
    def from_payload(cls, payload):
        """Creates a MessageP2P object from a payload string.

        This method creates a new P2P message object from the given payload
        string. It decodes the JSON payload, decodes any attachments, and
        returns a new MessageP2P instance.

        Args:
            payload (str): The JSON payload string.

        Returns:
            MessageP2P: A new MessageP2P object.
        """
        payload_message = json.loads(payload)
        attachments = list(map(cls.__decode_attachment__, payload_message['attachments']))
        return cls(payload_message['id'], payload_message['origin'], payload_message['destination'],
                   payload_message['body'], attachments)

    def get_id(self) -> str:
        """Generates a unique message ID.

        This method generates a unique ID for the message based on the
        origin, destination, and timestamp. It is used if no ID is provided
        during message creation.

        Returns:
            str: The generated message ID.
        """
        return f"{self.origin}_{self.destination}_{self.timestamp}"

    def __encode_attachment__(self, binary_attachment: dict):
        """Encodes an attachment using base64.

        This method takes a binary attachment dictionary (containing 'name',
        'data', and 'mime_type' keys) and base64-encodes the 'data' field.

        Args:
            binary_attachment (dict): The attachment dictionary to encode.

        Returns:
            dict: The encoded attachment dictionary.
        """
        encoded_attachment = binary_attachment.copy()
        encoded_attachment['data'] = str(base64.b64encode(binary_attachment['data']), 'utf-8')
        return encoded_attachment
    
    def __decode_attachment__(encoded_attachment: dict):
        """Decodes a base64-encoded attachment.

        This method takes an encoded attachment dictionary (containing
        'name', 'data', and 'mime_type' keys) and base64-decodes the
        'data' field.

        Args:
            encoded_attachment (dict): The attachment dictionary to decode.

        Returns:
            dict: The decoded attachment dictionary.
        """
        decoded_attachment = encoded_attachment.copy()
        decoded_attachment['data'] = base64.b64decode(encoded_attachment['data'])
        return decoded_attachment

    def to_dict(self):
        """Converts the message to a dictionary.

        This method converts the message object to a dictionary, encoding
        any attachments using base64. The resulting dictionary can be
        easily serialized to JSON or used for storage in a database.

        Returns:
            dict: A dictionary representation of the message.
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

