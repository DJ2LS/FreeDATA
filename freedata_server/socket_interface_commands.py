"""WORK IN PROGRESS by DJ2LS"""

from freedata_server.command_p2p_connection import P2PConnectionCommand
import structlog


class SocketCommandHandler:
    def __init__(self, cmd_request, ctx):
        self.logger = structlog.get_logger(type(self).__name__)
        self.cmd_request = cmd_request
        self.session = None
        self.ctx = ctx

    def log(self, message, isWarning=False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def send_response(self, message):
        try:
            self.log(f">>>>> {message}")
            full_message = f"{message}\r"
            self.cmd_request.sendall(full_message.encode())
        except Exception as e:
            self.log(f"Error sending to socket: {message}", isWarning=True)

    def handle_connect(self, data):
        try:
            params = {
                "origin": data[0],
                "destination": data[1],
            }

            cmd = P2PConnectionCommand(self.ctx, params)
            self.session = cmd.run()
            self.send_response("OK")
            self.send_response(f"REGISTERED {data[0]}")
            self.send_response("UNENCRYPTED LINK")
            self.ctx.socket_interface_manager.connecting_callsign = data[0]
            # if self.session.session_id:
            #    self.ctx.state_manager.register_p2p_connection_session(self.session)
            #    self.send_response("OK")
            #    self.session.connect()
            # else:
            #    self.send_response("ERROR")
        except Exception as e:
            self.send_response(f"ERR: {data}")

    def handle_disconnect(self, data):
        self.send_response("OK")
        try:
            self.session.disconnect()
        except Exception as e:
            self.log(f"Error disconnecting socket: {e}", isWarning=True)

    def handle_mycall(self, data):
        # Storing all of the callsigns assigned by client, to make sure they are checked later in new frames.
        self.ctx.socket_interface_manager.socket_interface_callsigns = data
        self.send_response("OK")
        self.send_response("UNENCRYPTED LINK")
        self.send_response("ENCRYPTION DISABLED")

    def handle_bw(self, data):
        # Logic for handling BW command
        self.ctx.socket_interface_manager.socket_interface_bandwidth = int(data[0])
        self.send_response("OK")

    def handle_abort(self, data):
        # Logic for handling ABORT command
        self.send_response("OK")
        try:
            self.session.abort_connection()
        except Exception as e:
            self.send_response(f"ERR: {e}")
        self.send_response("DISCONNECTED")

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
        # We are always sending OK, as we have our own compression
        self.send_response("OK")

    def handle_winlink_session(self, data):
        # Logic for handling WINLINK SESSION command
        # self.send_response(f"NOT IMPLEMENTED: {data}")
        self.send_response("OK")

    def handle_version(self, data):
        # Logic for handling VERSION command
        # maybe we need to use a different version, like 5.0
        self.send_response("VERSION FREEDATA")

    def socket_respond_disconnected(self):
        self.send_response("DISCONNECTED")

    def socket_respond_connected(self, origin, destination, bandwidth):
        print("[socket interface_commands] socket_respond_connected")
        if self.ctx.socket_interface_manager.connecting_callsign:
            # message = f"CONNECTED {self.ctx.socket_interface_manager.connecting_callsign} {destination} {bandwidth}"
            message = f"CONNECTED {origin} {destination} {bandwidth}"
        else:
            message = f"CONNECTED {origin} {destination} {bandwidth}"
        self.send_response("UNENCRYPTED LINK")
        self.send_response("LINK REGISTERED")
        self.send_response(message)

    def socket_respond_iamalive(self):
        try:
            self.send_response("IAMALIVE")
        except Exception as e:
            self.log(f"sending iamalive failed {e}")

    def socket_respond_buffer_size(self, buffer_size):
        self.send_response(f"BUFFER {buffer_size}")

    def socket_respond_ptt(self, state):
        """send the PTT state via command socket"""
        if state:
            message = "PTT ON"
        else:
            message = "PTT OFF"

        self.send_response(message)
