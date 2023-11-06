from flask import Flask, request, jsonify
from flask_sock import Sock
import os
import json
from config import CONFIG

app = Flask(__name__)
sock = Sock(app)

# set config file to use
def set_config():
    if 'FREEDATA_CONFIG' in os.environ:
        config_file = os.environ['FREEDATA_CONFIG']
    else:
        config_file = 'config.ini'

    if os.path.exists(config_file):
        print("Using config from %s" % config_file)
    else:
        print("Config file '%s' not found. Exiting." % config_file)
        exit(1)

    app.config_manager = CONFIG(config_file)

# returns a standard API response
def api_response(data, status = 'ok'):
    response = {
        'status': status,
        'data': data
    }
    return jsonify(response)

set_config()

## REST API
@app.route('/', methods=['GET'])
def index():
    return api_response({'name': 'FreeDATA API',
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
        return api_response(app.config_manager.read())

# Event websocket
@sock.route('/events')
def echo(sock):
    while True:
        data = sock.receive()
        sock.send(data)


