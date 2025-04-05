import base64
import json
import structlog

class EventManager:
    """Manages and broadcasts events within the FreeDATA server.

    This class handles the broadcasting of various events, including PTT
    changes, scatter changes, buffer overflows, custom events, ARQ session
    updates, and freedata_server status changes, to multiple queues. It
    provides a centralized mechanism for distributing event information
    throughout the application.
    """

    def __init__(self, queues):
        """Initializes the EventManager with a list of queues.

        Args:
            queues (list): A list of queues to which events will be broadcast.
        """
        self.queues = queues
        self.logger = structlog.get_logger('Event Manager')
        self.lastpttstate = False

    def broadcast(self, data):
        """Broadcasts an event to all registered queues.

        This method broadcasts the given event data to all queues registered
        with the EventManager. It clears a queue if its size exceeds 10 to
        prevent excessive queue buildup.

        Args:
            data: The event data to broadcast.
        """
        for q in self.queues:
            self.logger.debug(f"Event: ", ev=data)
            if q.qsize() > 10:
                q.queue.clear()
            q.put(data)

    def send_ptt_change(self, on:bool = False):
        """Sends a PTT change event.

        This method broadcasts a "ptt" event indicating whether the Push-to-Talk
        (PTT) is activated or deactivated. It avoids sending duplicate events
        by checking the last PTT state.

        Args:
            on (bool, optional): True if PTT is activated, False otherwise. Defaults to False.
        """
        if (on == self.lastpttstate):
            return
        self.lastpttstate= on
        self.broadcast({"ptt": bool(on)})

    def send_scatter_change(self, data):
        """Sends a scatter change event.

        This method broadcasts a "scatter" event containing the provided
        scatter data as a JSON string.

        Args:
            data: The scatter data to send.
        """
        self.broadcast({"scatter": json.dumps(data)})

    def send_buffer_overflow(self, data):
        """Sends a buffer overflow event.

        This method broadcasts a "buffer-overflow" event, indicating that a
        buffer overflow has occurred. The event data includes the provided
        data converted to a string.

        Args:
            data: The buffer overflow data to send.
        """
        self.broadcast({"buffer-overflow": str(data)})

    def send_custom_event(self, **event_data):
        """Sends a custom event.

        This method broadcasts a custom event with the provided keyword
        arguments as the event data. This allows for flexible creation and
        distribution of application-specific events.

        Args:
            **event_data: Keyword arguments representing the event data.
        """
        self.broadcast(event_data)

    def send_arq_session_new(self, outbound: bool, session_id, dxcall, total_bytes, state):
        """Sends an event for a new ARQ session.

        This method broadcasts an event indicating the start of a new ARQ
        (Automatic Repeat reQuest) session. The event includes information
        about the session's direction (inbound or outbound), session ID,
        destination callsign, total bytes to be transferred, and initial
        state.

        Args:
            outbound (bool): True if the session is outbound (sending data),
                False if it's inbound (receiving data).
            session_id: The unique ID of the ARQ session.
            dxcall (str): The callsign of the remote station.
            total_bytes (int): The total number of bytes to be transferred.
            state (str): The initial state of the ARQ session.
        """
        direction = 'outbound' if outbound else 'inbound'
        event = {
                "type": "arq",
                f"arq-transfer-{direction}": {
                'session_id': session_id,
                'dxcall': dxcall,
                'total_bytes': total_bytes,
                'state': state,
            }
        }
        self.broadcast(event)

    def send_arq_session_progress(self, outbound: bool, session_id, dxcall, received_bytes, total_bytes, state, speed_level, statistics=None):
        """Sends an ARQ session progress update event.

        This method broadcasts an event indicating the progress of an ARQ
        session. The event includes the session ID, destination callsign,
        received and total bytes, current state, speed level, and any
        relevant statistics.

        Args:
            outbound (bool): True if the session is outbound, False otherwise.
            session_id: The ID of the ARQ session.
            dxcall (str): The callsign of the remote station.
            received_bytes (int): The number of bytes received so far.
            total_bytes (int): The total number of bytes to be transferred.
            state (str): The current state of the ARQ session.
            speed_level: The current speed level of the ARQ session.
            statistics (dict, optional): A dictionary containing session statistics. Defaults to None.
        """
        if statistics is None:
            statistics = {}

        direction = 'outbound' if outbound else 'inbound'
        event = {
                "type": "arq",
                f"arq-transfer-{direction}": {
                'session_id': session_id,
                'dxcall': dxcall,
                'received_bytes': received_bytes,
                'total_bytes': total_bytes,
                'state': state,
                'speed_level': speed_level,
                'statistics': statistics,
            }
        }
        self.broadcast(event)

    def send_arq_session_finished(self, outbound: bool, session_id, dxcall, success: bool, state: bool, data=False, statistics=None):
        """Sends an ARQ session finished event.

        This method broadcasts an event indicating the completion of an ARQ
        session. The event includes information about the session's direction,
        ID, destination callsign, success status, final state, data
        (if any), and statistics. It base64-encodes any data included in
        the event.

        Args:
            outbound (bool): True if the session was outbound, False otherwise.
            session_id: The ID of the ARQ session.
            dxcall (str): The callsign of the remote station.
            success (bool): True if the session completed successfully, False otherwise.
            state (str): The final state of the ARQ session.
            data (any, optional): The data transferred during the session. Defaults to False.
            statistics (dict, optional): A dictionary of session statistics. Defaults to None.
        """
        if statistics is None:
            statistics = {}
        if data:
            if isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
                # Base64 encode the bytes-like object
            data = base64.b64encode(data).decode("UTF-8")
        direction = 'outbound' if outbound else 'inbound'
        event = {
                "type" : "arq",
                f"arq-transfer-{direction}": {
                'session_id': session_id,
                'dxcall': dxcall,
                'statistics': statistics,
                'success': bool(success),
                'state': state,
                'data': data
            }
        }
        self.broadcast(event)

    def modem_started(self):
        """Sends a freedata_server started event.

        This method broadcasts an event indicating that the FreeDATA freedata_server
        has started successfully.
        """
        event = {"freedata_server": "started"}
        self.broadcast(event)

    def modem_restarted(self):
        """Sends a freedata_server restarted event.

        This method broadcasts an event indicating that the FreeDATA freedata_server
        has been restarted.
        """
        event = {"freedata_server": "restarted"}
        self.broadcast(event)

    def modem_stopped(self):
        """Sends a freedata_server stopped event.

        This method broadcasts an event indicating that the FreeDATA freedata_server
        has stopped.
        """
        event = {"freedata_server": "stopped"}
        self.broadcast(event)

    def modem_failed(self):
        """Sends a freedata_server failed event.

        This method broadcasts an event indicating that the FreeDATA freedata_server
        has failed to start or has encountered an error.
        """
        event = {"freedata_server": "failed"}
        self.broadcast(event)

    def freedata_message_db_change(self, message_id=None):
        """Sends a FreeDATA message database change event.

        This method broadcasts an event indicating that the FreeDATA message
        database has been changed. The event includes the ID of the message
        that triggered the change, if available.

        Args:
            message_id (any, optional): The ID of the changed message. Defaults to None.
        """
        self.broadcast({"message-db": "changed", "message_id": message_id})

    def freedata_logging(self, type, status, message):
        """Broadcasts a FreeDATA logging event.

        This method broadcasts an event related to FreeDATA logging,
        indicating the type of logging endpoint and its status. It is
        used to inform other parts of the application about logging
        activities.

        Args:
            type (str): The type of logging endpoint (e.g., "file", "websocket").
            status (any): The status of the logging operation.
            message (str): The message to be displayed
        """

        self.broadcast({"type": "message-logging", "endpoint": type, "status": status, "message": message})
