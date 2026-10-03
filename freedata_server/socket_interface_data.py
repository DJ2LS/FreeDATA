"""WORK IN PROGRESS by DJ2LS"""


class SocketDataHandler:
    def __init__(self, cmd_request, ctx):
        self.cmd_request = cmd_request
        self.ctx = ctx
        self.session = None

    def send_response(self, message):
        full_message = f"{message}\r"
        self.cmd_request.sendall(full_message.encode())

    def send_data_to_client(self, data):
        # data port is binary transparent, so send the payload unmodified
        self.cmd_request.sendall(data)
