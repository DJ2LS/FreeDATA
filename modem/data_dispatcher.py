import json
import structlog
class DataDispatcher:
    def __init__(self):
        self.logger = structlog.get_logger(type(self).__name__)

        # endpoints
        self.endpoints = {
            "p2pmsg": self.handle_p2pmsg,
            "test": self.handle_test,
        }

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

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
                    return key, value  # Return type and data
            return "raw", byte_data  # Treat as raw data if no matching type is found
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "raw", byte_data  # Return original data as raw if there's an error

    def dispatch(self, byte_data):
        """Decapsulate and dispatch data to the appropriate endpoint based on its type."""
        type_key, data = self.decapsulate(byte_data)
        if type_key in self.endpoints:
            self.endpoints[type_key](data)
        else:
            # Use the default handler for unrecognized types
            self.handle_raw(data)

    def handle_p2pmsg(self, data):
        self.log(f"Handling p2pmsg: {data}")

    def handle_raw(self, data):
        self.log(f"Handling raw data: {data}")

    def handle_test(self, data):
        self.log(f"Handling test data: {data}")