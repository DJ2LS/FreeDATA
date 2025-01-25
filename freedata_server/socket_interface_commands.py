""" WORK IN PROGRESS by DJ2LS"""
from command_p2p_connection import P2PConnectionCommand

class SocketCommandHandler:

    def __init__(self, cmd_request, modem, config_manager, state_manager, event_manager, socket_interface_manager):
        self.cmd_request = cmd_request
        self.modem = modem
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.socket_interface_manager = socket_interface_manager
        self.session = None

    def send_response(self, message):
        full_message = f"{message}\r"
        self.cmd_request.sendall(full_message.encode())

    def handle_connect(self, data):
        try:
            params = {
                'origin': data[0],
                'destination': data[1],
            }

            # TODO "self" was expected to be the socket_command_handler, but its not making sense, we are always passing the socket_interface_manager, means the entire socket instance.
            # so we need to find a way, passing the socket_interface_manager instead

            cmd = P2PConnectionCommand(self.config_manager.read(), self.state_manager, self.event_manager, params, self.socket_interface_manager)
            self.session = cmd.run(self.event_manager.queues, self.modem)
            print(self.session.session_id)
            #if self.session.session_id:
            #    self.state_manager.register_p2p_connection_session(self.session)
            #    self.send_response("OK")
            #    self.session.connect()
            #else:
            #    self.send_response("ERROR")
        except:
            self.send_response(f"ERR: {data}")

    def handle_disconnect(self, data):
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_mycall(self, data):
        # Logic for handling MYCALL command
        print()
        #self.socket_interface_manager.socket_interface_callsigns = data
        self.send_response(f"OK")

    def handle_bw(self, data):
        # Logic for handling BW command
        #self.socket_interface_manager.bandwidth = data
        self.send_response(f"OK")

    def handle_abort(self, data):
        # Logic for handling ABORT command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_public(self, data):
        # Logic for handling PUBLIC command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_cwid(self, data):
        # Logic for handling CWID command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_listen(self, data):
        # Logic for handling LISTEN command
        self.send_response(f"OK")

    def handle_compression(self, data):
        # Logic for handling COMPRESSION command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_winlink_session(self, data):
        # Logic for handling WINLINK SESSION command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def socket_respond_disconnected(self):
        self.send_response("DISCONNECTED")

    def socket_respond_connected(self, mycall, dxcall, bandwidth):
        print("[socket interface_commands] socket_respond_connected")
        if self.session.is_ISS:
            message = f"CONNECTED {mycall} {dxcall} {bandwidth}"
        else:
            message = f"CONNECTED {dxcall} {mycall} {bandwidth}"
        self.send_response(message)

    def socket_respond_ptt(self, state):
        """ send the PTT state via command socket"""
        if state:
            message = f"PTT ON"
        else:
            message = f"PTT OFF"

        self.send_response(message)
