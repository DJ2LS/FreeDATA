import socketserver
import threading
import logging
import structlog
import select
from queue import Queue

from command_p2p_connection import P2PConnectionCommand

# Shared queue for command and data handlers
data_queue = Queue()

class CommandHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.logger = structlog.get_logger(type(self).__name__)

        self.handlers = {
            'CONNECT': self.handle_connect,
            'DISCONNECT': self.handle_disconnect,
            'MYCALL': self.handle_mycall,
            'BW': self.handle_bw,
            'ABORT': self.handle_abort,
            'PUBLIC': self.handle_public,
            'CWID': self.handle_cwid,
            'LISTEN': self.handle_listen,
            'COMPRESSION': self.handle_compression,
            'WINLINK SESSION': self.handle_winlink_session,
        }
        super().__init__(request, client_address, server)

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def handle(self):
        self.log(f"Client connected: {self.client_address}")
        try:
            while True:
                data = self.request.recv(1024).strip()
                if not data:
                    break
                decoded_data = data.decode()
                self.log(f"Command received from {self.client_address}: {decoded_data}")
                self.parse_command(decoded_data)
        finally:
            self.log(f"Command connection closed with {self.client_address}")

    def parse_command(self, data):
        for command in self.handlers:
            if data.startswith(command):
                # Extract command arguments after the command itself
                args = data[len(command):].strip().split()
                self.dispatch_command(command, args)
                return
        self.send_response("ERROR: Unknown command\r\n")

    def dispatch_command(self, command, data):
        if command in self.handlers:
            handler = self.handlers[command]
            handler(data)
        else:
            self.send_response(f"Unknown command: {command}")

    def send_response(self, message):
        self.request.sendall(message.encode())

    # Command handlers
    def handle_connect(self, data):
        # Your existing connect logic
        self.send_response("OK\r\n")

    def handle_disconnect(self, data):
        # Your existing disconnect logic
        self.send_response("OK\r\n")

    def handle_mycall(self, data):
        # Logic for handling MYCALL command
        self.send_response("OK\r\n")

    def handle_bw(self, data):
        # Logic for handling BW command
        self.send_response("OK\r\n")

    def handle_abort(self, data):
        # Logic for handling ABORT command
        self.send_response("OK\r\n")

    def handle_public(self, data):
        # Logic for handling PUBLIC command
        self.send_response("OK\r\n")

    def handle_cwid(self, data):
        # Logic for handling CWID command
        self.send_response("OK\r\n")

    def handle_listen(self, data):
        # Logic for handling LISTEN command
        self.send_response("OK\r\n")

    def handle_compression(self, data):
        # Logic for handling COMPRESSION command
        self.send_response("OK\r\n")

    def handle_winlink_session(self, data):
        # Logic for handling WINLINK SESSION command
        self.send_response("OK\r\n")

class DataHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.logger = structlog.get_logger(type(self).__name__)

        super().__init__(request, client_address, server)

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)
    def handle(self):
        self.log(f"Data connection established with {self.client_address}")

        try:
            while True:
                ready_to_read, _, _ = select.select([self.request], [], [], 1)  # 1-second timeout
                if ready_to_read:
                    self.data = self.request.recv(1024).strip()
                    if not self.data:
                        break
                    try:
                        self.log(f"Data received from {self.client_address}: [{len(self.data)}] - {self.data.decode()}")
                    except:
                        self.log(f"Data received from {self.client_address}: [{len(self.data)}] - {self.data}")

                # Check if there's something to send from the queue, without blocking
                if not data_queue.empty():
                    data_to_send = data_queue.get_nowait()  # Use get_nowait to avoid blocking
                    self.request.sendall(data_to_send)
                    self.log(f"Sent data to {self.client_address}")

        finally:
            self.log(f"Data connection closed with {self.client_address}")
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


class SocketInterfaceHandler:
    def __init__(self, config, state_manager):
        self.config = config
        self.state_manager = state_manager
        self.logger = structlog.get_logger(type(self).__name__)
        self.command_port = self.config["SOCKET_INTERFACE"]["cmd_port"]
        self.data_port = self.config["SOCKET_INTERFACE"]["data_port"]
        self.command_server = None
        self.data_server = None
        self.command_server_thread = None
        self.data_server_thread = None

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def start_servers(self):
        # Method to start both command and data server threads
        self.command_server_thread = threading.Thread(target=self.run_server, args=(self.command_port, CommandHandler))
        self.data_server_thread = threading.Thread(target=self.run_server, args=(self.data_port, DataHandler))

        self.command_server_thread.start()
        self.data_server_thread.start()

        self.log(f"Interfaces started")

    def run_server(self, port, handler):
        with ThreadedTCPServer(('127.0.0.1', port), handler) as server:
            self.log(f"Server started on port {port}")
            if port == self.command_port:
                self.command_server = server
            else:
                self.data_server = server
            server.serve_forever()

    def stop_servers(self):
        # Gracefully shutdown the server
        if self.command_server:
            self.command_server.shutdown()
        if self.data_server:
            self.data_server.shutdown()
        self.log(f"Interfaces stopped")

    def wait_for_server_threads(self):
        # Wait for both server threads to finish
        self.command_server_thread.join()
        self.data_server_thread.join()
