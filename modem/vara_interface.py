import socketserver
import threading
import logging
import signal
import sys
import select
from queue import Queue

from command_p2p_connection import P2PConnectionCommand

# Shared queue for command and data handlers
data_queue = Queue()
# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class VARACommandHandler(socketserver.BaseRequestHandler):
    mycall = None  # Class attribute to store mycall
    dxcall = None
    bandwidth = None  # Class attribute to store bandwidth


    def handle(self):
        logging.info(f"Command connection established with {self.client_address}")
        try:
            while True:
                self.data = self.request.recv(1024).strip()
                if not self.data:
                    break
                logging.info(f"Command received from {self.client_address}: {self.data}")

                if self.data.startswith(b'MYCALL '):
                    VARACommandHandler.mycall = self.data.split(b' ')[1].strip()
                    self.request.sendall(b"OK\r\n")
                elif self.data.startswith(b'BW'):
                    VARACommandHandler.bandwidth = self.data[2:].strip()
                    self.request.sendall(b"OK\r\n")
                elif self.data.startswith(b'CONNECT '):

                    P2PConnectionCommand.connect('MYCALL', 'DXCALL', 'BANDWIDTH')

                    self.request.sendall(b"OK\r\n")
                    parts = self.data.split()
                    if len(parts) >= 3 and VARACommandHandler.mycall and VARACommandHandler.bandwidth:
                        VARACommandHandler.dxcall = parts[2]
                        # Using the stored mycall and bandwidth for the response
                        bytestring = b'CONNECTED ' + VARACommandHandler.mycall + b' ' + VARACommandHandler.dxcall + b' ' + VARACommandHandler.bandwidth + b'\r\n'
                        self.request.sendall(bytestring)

                    else:
                        self.request.sendall(b"ERROR: MYCALL or Bandwidth not set.\r\n")
                elif self.data.startswith(b'ABORT'):
                    bytestring = b'DISCONNECTED\r\n'
                elif self.data.startswith(b'DISCONNECT'):
                    bytestring = b'DISCONNECTED\r\n'
                    self.request.sendall(bytestring)
                else:
                    self.request.sendall(b"OK\r\n")

        finally:
            logging.info(f"Command connection closed with {self.client_address}")


class VARADataHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logging.info(f"Data connection established with {self.client_address}")

        try:
            while True:
                ready_to_read, _, _ = select.select([self.request], [], [], 1)  # 1-second timeout
                if ready_to_read:
                    self.data = self.request.recv(1024).strip()
                    if not self.data:
                        break
                    try:
                        logging.info(f"Data received from {self.client_address}: [{len(self.data)}] - {self.data.decode()}")
                    except:
                        logging.info(f"Data received from {self.client_address}: [{len(self.data)}] - {self.data}")



                # Check if there's something to send from the queue, without blocking
                if not data_queue.empty():
                    data_to_send = data_queue.get_nowait()  # Use get_nowait to avoid blocking
                    self.request.sendall(data_to_send)
                    logging.info(f"Sent data to {self.client_address}")

        finally:
            logging.info(f"Data connection closed with {self.client_address}")
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def run_server(port, handler):
    with ThreadedTCPServer(('127.0.0.1', port), handler) as server:
        logging.info(f"Server running on port {port}")
        server.serve_forever()


def signal_handler(sig, frame):
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Create server threads for command and data ports
    command_server_thread = threading.Thread(target=run_server, args=(8300, VARACommandHandler))
    data_server_thread = threading.Thread(target=run_server, args=(8301, VARADataHandler))

    # Start the server threads
    command_server_thread.start()
    data_server_thread.start()

    # Wait for both server threads to finish
    command_server_thread.join()
    data_server_thread.join()
