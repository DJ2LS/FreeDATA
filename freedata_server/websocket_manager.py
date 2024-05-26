import threading
import json
import asyncio

# WebSocket client sets
events_client_list = set()
fft_client_list = set()
states_client_list = set()

async def handle_connection(websocket, client_list, event_queue):
    client_list.add(websocket)
    while True:
        try:
            await websocket.receive_text()
        except Exception as e:
            print(f"Client connection lost: {e}")
            try:
                client_list.remove(websocket)
            except Exception as err:
                print(f"Error removing client from list: {e} | {err}")
            break

def transmit_sock_data_worker(client_list, event_queue):
    while True:
        event = event_queue.get()
        json_event = json.dumps(event)
        clients = client_list.copy()
        for client in clients:
            try:
                asyncio.run(client.send_text(json_event))
            except Exception:
                client_list.remove(client)

def startWorkerThreads(app):
    events_thread = threading.Thread(target=transmit_sock_data_worker, daemon=True, args=(events_client_list, app.modem_events))
    events_thread.start()

    states_thread = threading.Thread(target=transmit_sock_data_worker, daemon=True, args=(states_client_list, app.state_queue))
    states_thread.start()

    fft_thread = threading.Thread(target=transmit_sock_data_worker, daemon=True, args=(fft_client_list, app.modem_fft))
    fft_thread.start()
