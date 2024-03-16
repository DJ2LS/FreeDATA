import socketserver
import threading
import structlog
import select
from queue import Queue
from socket_interface_commands import SocketCommandHandler

# Shared queue for command and data handlers
data_queue = Queue()

class CommandSocket(socketserver.BaseRequestHandler):
    #def __init__(self, request, client_address, server):
    def __init__(self, request, client_address, server, state_manager=None, event_manager=None):
        self.state_manager = state_manager

        self.logger = structlog.get_logger(type(self).__name__)

        self.command_handler = SocketCommandHandler(request, self.state_manager)

        self.handlers = {
            'CONNECT': self.command_handler.handle_connect,
            'DISCONNECT': self.command_handler.handle_disconnect,
            'MYCALL': self.command_handler.handle_mycall,
            'BW': self.command_handler.handle_bw,
            'ABORT': self.command_handler.handle_abort,
            'PUBLIC': self.command_handler.handle_public,
            'CWID': self.command_handler.handle_cwid,
            'LISTEN': self.command_handler.handle_listen,
            'COMPRESSION': self.command_handler.handle_compression,
            'WINLINK SESSION': self.command_handler.handle_winlink_session,
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



class DataSocket(socketserver.BaseRequestHandler):
    #def __init__(self, request, client_address, server):
    def __init__(self, request, client_address, server, state_manager=None, event_manager=None):
        self.state_manager = state_manager

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


#class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
#    allow_reuse_address = True


class CustomThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, **kwargs):
        self.extra_args = kwargs
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, **self.extra_args)

class SocketInterfaceHandler:
    def __init__(self, config, state_manager, event_manager):
        self.config = config
        self.state_manager = state_manager
        self.event_manager = event_manager
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
        self.command_server_thread = threading.Thread(target=self.run_server, args=(self.command_port, CommandSocket))
        self.data_server_thread = threading.Thread(target=self.run_server, args=(self.data_port, DataSocket))

        self.command_server_thread.start()
        self.data_server_thread.start()

        self.log(f"Interfaces started")

    def run_server(self, port, handler):
        with CustomThreadedTCPServer(('127.0.0.1', port), handler, state_manager=self.state_manager, event_manager=self.event_manager) as server:
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
