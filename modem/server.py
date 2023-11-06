from flask import Flask, request, jsonify
from flask_sock import Sock
import argparse, json
from config import CONFIG

app = Flask(__name__)
sock = Sock(app)

# CLI arguments
def get_config_filename_from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help = "Specifiy config file", default = 'config.ini') 
    args, unknown = parser.parse_known_args()
    return args.config

config = CONFIG(get_config_filename_from_args())

def api_response(data, status = 'ok'):
    response = {
        'status': status,
        'data': data
    }
    return jsonify(response)

## REST API
@app.route('/', methods=['GET'])
def index():
    return jsonify({'name': 'FreeDATA API',
                    'description': '',
                    'api_version': 1,
                    'license': 'GPL3.0',
                    'documentation': 'https://wiki.freedata.app',
                    })

# get and set config
@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        new_config = json.loads(request.form['config'])
        set_config = config.write(new_config)
        if not set_config:
            response = api_response(None, 'error writing config')
        else:
            response = api_response(set_config)
        return response
    elif request.method == 'GET':
        return api_response(config.read())

# get activity
@app.route('/activity', methods=['GET'])
def activity():
    return "Not implemented yet."

# get received messages
@app.route('/messages', methods=['GET'])
def messages():
    return "Not implemented yet."

# new message / delete message
""" @app.route('/message', methods=['POST', 'DELETE'])
def message():
    if request.method == 'POST':
      message = new Message(request.form['message'])
      status = modem.send_message(message)
    elif request.method == 'DELETE':
      status = messageDb.deleteMessage(request.form['id'])
    return status
 """
# Event websocket
@sock.route('/events')
def echo(sock):
    while True:
        data = sock.receive()
        sock.send(data)


