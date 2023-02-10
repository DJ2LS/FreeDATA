import sock
import threading
import ujson as json


received_json =b'{"type": "command", "command": "start_beacon", "parameter": "5"}'

sock.TESTMODE = True
#sock.ThreadedTCPRequestHandler.process_tnc_commands(None, received_json)

#testserver = sock.ThreadedTCPServer(('127.0.0.1', 3000), sock.ThreadedTCPRequestHandler).serve_forever
#server_thread = threading.Thread(target=testserver.serve_forever)
#server_thread.daemon = True
#server_thread.start()


#test = sock.ThreadedTCPRequestHandler(request=sock.ThreadedTCPServer, client_address='127.0.0.1', server=None)

#sock.process_tnc_commands(received_json)
sock.ThreadedTCPRequestHandler.process_tnc_commands(None, received_json)



print("done")