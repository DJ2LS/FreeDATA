""" WORK IN PROGRESS by DJ2LS"""
from command_p2p_connection import P2PConnectionCommand

class SocketCommandHandler:

    def __init__(self, cmd_request, modem, config_manager, state_manager, event_manager):
        self.cmd_request = cmd_request
        self.modem = modem
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.event_manager = event_manager

        self.session = None

    def send_response(self, message):
        full_message = f"{message}\r\n"
        self.cmd_request.sendall(full_message.encode())

    def handle_connect(self, data):

        params = {
            'origin': data[0],
            'destination': data[1],
        }
        cmd = P2PConnectionCommand(self.config_manager.read(), self.state_manager, self.event_manager, params, self)
        self.session = cmd.run(self.event_manager.queues, self.modem)

        #if self.session.session_id:
        #    self.state_manager.register_p2p_connection_session(self.session)
        #    self.send_response("OK")
        #    self.session.connect()
        #else:
        #    self.send_response("ERROR")

    def handle_disconnect(self, data):
        # Your existing connect logic
        self.send_response("OK")

    def handle_mycall(self, data):
        # Logic for handling MYCALL command
        self.send_response("OK")

    def handle_bw(self, data):
        # Logic for handling BW command
        self.send_response("OK")

    def handle_abort(self, data):
        # Logic for handling ABORT command
        self.send_response("OK")

    def handle_public(self, data):
        # Logic for handling PUBLIC command
        self.send_response("OK")

    def handle_cwid(self, data):
        # Logic for handling CWID command
        self.send_response("OK")

    def handle_listen(self, data):
        # Logic for handling LISTEN command
        self.send_response("OK")

    def handle_compression(self, data):
        # Logic for handling COMPRESSION command
        self.send_response("OK")

    def handle_winlink_session(self, data):
        # Logic for handling WINLINK SESSION command
        self.send_response("OK")

    def socket_respond_disconnected(self):
        self.send_response("DISCONNECTED")

    def socket_respond_connected(self, mycall, dxcall, bandwidth):
        message = f"CONNECTED {mycall} {dxcall} {bandwidth}"
        self.send_response(message)
