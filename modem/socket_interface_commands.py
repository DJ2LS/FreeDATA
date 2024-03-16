from command_p2p_connection import P2PConnectionCommand

class SocketCommandHandler:

    def __init__(self, request, state_manager):
        self.request = request
        self.state_manager = state_manager

        print(self.state_manager)


    def send_response(self, message):
        self.request.sendall(message.encode())



    def handle_connect(self, data):
        # Your existing connect logic
        self.send_response("OK\r\n")

        params = {
            'destination': "BB2BBB-2",
            'origin': "AA1AAA-1",
        }
        cmd = P2PConnectionCommand(self.config, self.iss_state_manager, self.iss_event_queue, params)
        session = cmd.run(self.iss_event_queue, self.iss_modem)
        if session.session_id:
            self.iss_state_manager.register_p2p_connection_session(session)
            session.connect()




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