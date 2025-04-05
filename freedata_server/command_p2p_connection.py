import queue
from command import TxCommand
import api_validations
import base64
from queue import Queue
from p2p_connection import P2PConnection

class P2PConnectionCommand(TxCommand):
    """Command to initiate a P2P connection.

    This command sets up a P2P connection between two stations, handling
    session creation, registration, and connection establishment.
    """

    def set_params_from_api(self, apiParams):
        """Sets parameters from the API request.

        This method extracts the origin and destination callsigns from the
        API parameters and validates them, adding a default SSID if necessary.

        Args:
            apiParams (dict): A dictionary containing the API parameters.
        """
        self.origin = apiParams['origin']
        if not api_validations.validate_freedata_callsign(self.origin):
            self.origin = f"{self.origin}-0"

        self.destination = apiParams['destination']
        if not api_validations.validate_freedata_callsign(self.destination):
            self.destination = f"{self.destination}-0"


    def connect(self, event_queue: Queue, modem):
        """Placeholder for the connect method.

        This method is currently not implemented and serves as a placeholder
        for future functionality related to P2P connection establishment.

        Args:
            event_queue (Queue): The event queue.
            modem: The modem object.
        """
        pass

    def run(self, event_queue: Queue, modem):
        """Executes the P2P connection command.

        This method creates a P2PConnection session, registers it with the
        state manager, initiates the connection, and handles potential errors
        during session startup.

        Args:
            event_queue (Queue): The event queue.
            modem: The modem object.

        Returns:
            P2PConnection or bool: The P2PConnection object if successful, False otherwise.
        """
        try:
            self.emit_event(event_queue)
            session = P2PConnection(self.config, modem, self.origin, self.destination, self.state_manager, self.event_manager, self.socket_interface_manager)
            print(session)
            if session.session_id:
                self.state_manager.register_p2p_connection_session(session)
                session.connect()
                return session
            return False

        except Exception as e:
            self.log(f"Error starting P2P Connection session: {e}", isWarning=True)

        return False