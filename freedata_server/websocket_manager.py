import threading
import json
import asyncio
import structlog


class wsm:
    """Manages WebSocket connections and data transmission.

    This class handles WebSocket connections from clients, manages client
    lists for different data types (events, FFT, states), and transmits
    data to connected clients via worker threads. It ensures a clean
    shutdown of WebSocket connections and related resources.
    """
    def __init__(self):
        """Initializes the WebSocket manager.

        This method sets up the logger, shutdown flag, client lists for
        different data types, and worker threads.
        """
        self.log = structlog.get_logger("WEBSOCKET_MANAGER")
        self.shutdown_flag = threading.Event()

        # WebSocket client sets
        self.events_client_list = set()
        self.fft_client_list = set()
        self.states_client_list = set()

        self.events_thread = None
        self.states_thread = None
        self.fft_thread = None
        
    async def handle_connection(self, websocket, client_list, event_queue):
        """Handles a WebSocket connection.

        This method adds the new client to the provided list and continuously
        listens for incoming messages. If a client disconnects, it removes
        the client from the list and logs the event.

        Args:
            websocket: The WebSocket object representing the client connection.
            client_list (set): The set of connected WebSocket clients.
            event_queue (queue.Queue): The event queue. Currently unused.
        """
        client_list.add(websocket)
        while not self.shutdown_flag.is_set():
            try:
                await websocket.receive_text()
            except Exception as e:
                self.log.warning(f"Client connection lost", e=e)
                try:
                    client_list.remove(websocket)
                except Exception as err:
                    self.log.error(f"Error removing client from list", e=e, err=err)
                break

    def transmit_sock_data_worker(self, client_list, event_queue):
        """Worker thread function for transmitting data to WebSocket clients.

        This method continuously retrieves events from the provided queue and
        sends them as JSON strings to all connected clients in the specified
        list. It handles client disconnections gracefully.

        Args:
            client_list (set): The set of connected WebSocket clients.
            event_queue (queue.Queue): The queue containing events to be transmitted.
        """
        while not self.shutdown_flag.is_set():
            try:
                event = event_queue.get(timeout=1)

                if event:
                    json_event = json.dumps(event)
                    clients = client_list.copy()
                    for client in clients:
                        try:
                            asyncio.run(client.send_text(json_event))
                        except Exception:
                            client_list.remove(client)
            except Exception:
                continue



    def startWorkerThreads(self, app):
        """Starts worker threads for handling WebSocket data transmission.

        This method creates and starts daemon threads for transmitting modem
        events, state updates, and FFT data to connected WebSocket clients.
        Each thread uses the transmit_sock_data_worker method to send data
        from the respective queues to the appropriate client lists.

        Args:
            app: The main application object containing the event queues and client lists.
        """
        self.events_thread = threading.Thread(target=self.transmit_sock_data_worker, daemon=True, args=(self.events_client_list, app.modem_events))
        self.events_thread.start()

        self.states_thread = threading.Thread(target=self.transmit_sock_data_worker, daemon=True, args=(self.states_client_list, app.state_queue))
        self.states_thread.start()

        self.fft_thread = threading.Thread(target=self.transmit_sock_data_worker, daemon=True, args=(self.fft_client_list, app.modem_fft))
        self.fft_thread.start()
        
    def shutdown(self):
        """Shuts down the WebSocket manager.

        This method sets the shutdown flag, waits for worker threads to
        finish, and logs the shutdown process. It ensures a clean shutdown
        of WebSocket connections and related threads.
        """
        self.log.warning("[SHUTDOWN] closing websockets...")
        self.shutdown_flag.set()
        self.events_thread.join(0.5)
        self.states_thread.join(0.5)
        self.fft_thread.join(0.5)
        self.log.warning("[SHUTDOWN] websockets closed")