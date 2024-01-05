import threading
import json

# websocket multi client support for using with queued information.
# our client set which contains all connected websocket clients
events_client_list = set()
fft_client_list = set()
states_client_list = set()

def handle_connection(sock, client_list, event_queue):
    event_queue.put({"type": "hello-client"})
    
    client_list.add(sock)
    while True:
        try:
            sock.receive(timeout=1)
        except Exception as e:
            print(f"client connection lost: {e}")
            try:
                client_list.remove(sock)
            except Exception as err:
                print(f"error removing client from list: {e} | {err}")
            break
    return

def transmit_sock_data_worker(client_list, event_queue):
    while True:
        event = event_queue.get()
        if isinstance(event, str):
            print(f"WARNING: Queue event:\n'{event}'\n still in string format")
            json_event = event
        else:
            json_event = json.dumps(event)
        clients = client_list.copy()
        for client in clients:
            try:
                client.send(json_event)
            except Exception:
                client_list.remove(client)

# start a worker thread for every socket endpoint
def startThreads(app):
    events_thread = threading.Thread(target=transmit_sock_data_worker, daemon=True, args=(events_client_list, app.modem_events))
    events_thread.start()

    states_thread = threading.Thread(target=transmit_sock_data_worker, daemon=True, args=(states_client_list, app.state_queue))
    states_thread.start()

    fft_thread = threading.Thread(target=transmit_sock_data_worker, daemon=True, args=(fft_client_list, app.modem_fft))
    fft_thread.start()