import threading
import json
import asyncio



class wsm:
    def __init__(self):
        self.shutdown_flag = threading.Event()

        # WebSocket client sets
        self.events_client_list = set()
        self.fft_client_list = set()
        self.states_client_list = set()
        
    async def handle_connection(self, websocket, client_list, event_queue):
        client_list.add(websocket)
        while not self.shutdown_flag.is_set():
            try:
                await websocket.receive_text()
            except Exception as e:
                print(f"Client connection lost: {e}")
                try:
                    client_list.remove(websocket)
                except Exception as err:
                    print(f"Error removing client from list: {e} | {err}")
                break

    def transmit_sock_data_worker(self, client_list, event_queue):
        while not self.shutdown_flag.is_set():
            event = event_queue.get()
            json_event = json.dumps(event)
            clients = client_list.copy()
            for client in clients:
                try:
                    asyncio.run(client.send_text(json_event))
                except Exception:
                    client_list.remove(client)
    
    def startWorkerThreads(self, app):
        events_thread = threading.Thread(target=self.transmit_sock_data_worker, daemon=True, args=(self.events_client_list, app.modem_events))
        events_thread.start()
    
        states_thread = threading.Thread(target=self.transmit_sock_data_worker, daemon=True, args=(self.states_client_list, app.state_queue))
        states_thread.start()
    
        fft_thread = threading.Thread(target=self.transmit_sock_data_worker, daemon=True, args=(self.fft_client_list, app.modem_fft))
        fft_thread.start()
        
    def shutdown(self):
        self.shutdown_flag = threading.Event().set()