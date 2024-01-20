# File: arq_data_formatter.py

import json

class ARQDataFormatter:
    def __init__(self):
        pass

    def encapsulate(self, data, type_key="p2pmsg"):
        """Encapsulate data into the specified format with the given type key."""
        formatted_data = {type_key: data}
        return json.dumps(formatted_data)

    def decapsulate(self, byte_data):
        """Decapsulate data from the specified format, returning both the data and the type."""
        try:
            json_data = byte_data.decode('utf-8')  # Decode byte array to string
            parsed_data = json.loads(json_data)
            if parsed_data and isinstance(parsed_data, dict):
                for key, value in parsed_data.items():
                    return key, value
            return "raw", byte_data
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "raw", byte_data
