from flask import Flask, request, jsonify
from flask_sock import Sock
from flask_cors import CORS
import os
import serial_ports
from config import CONFIG
import audio
import data_handler
import modem
import queue

app = Flask(__name__)
CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})
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

# start modem
app.modem_events = queue.Queue()
app.modem = modem.RF(app.config_manager.config, app.modem_events)
data_handler.DATA(app.config_manager.config, app.modem_events)

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
        set_config = app.config_manager.write(request.json)
        if not set_config:
            response = api_response(None, 'error writing config')
        else:
            response = api_response(set_config)
        return response
    elif request.method == 'GET':
        return api_response(app.config_manager.read())

@app.route('/devices/audio', methods=['GET'])
def get_audio_devices():
    dev_in, dev_out = audio.get_audio_devices()
    devices = { 'in': dev_in, 'out': dev_out }
    return api_response(devices)

@app.route('/devices/serial', methods=['GET'])
def get_serial_devices():
    devices = serial_ports.get_ports()
    return api_response(devices)

# @app.route('/modem/listen', methods=['POST'])
# @app.route('/modem/record_audio', methods=['POST'])
# @app.route('/modem/responde_to_call', methods=['POST'])
# @app.route('/modem/responde_to_cq', methods=['POST'])
# @app.route('/modem/audio_levels', methods=['POST']) # tx and rx
# @app.route('/modem/send_test_frame', methods=['POST'])
# @app.route('/modem/fec_transmit', methods=['POST'])
# @app.route('/modem/fec_is_writing', methods=['POST'])
# @app.route('/modem/cqcqcq', methods=['POST'])
# @app.route('/modem/beacon', methods=['POST']) # on/off
# @app.route('/modem/mesh_ping', methods=['POST'])
# @app.route('/modem/ping_ping', methods=['POST'])
# @app.route('/modem/arc_connect', methods=['POST'])
# @app.route('/modem/arc_disconnect', methods=['POST'])
# @app.route('/modem/send_raw', methods=['POST'])
# @app.route('/modem/stop_transmission', methods=['POST'])

# @app.route('/mesh/routing_table', methods=['GET'])
# @app.route('/modem/get_rx_buffer', methods=['GET'])
# @app.route('/modem/del_rx_buffer', methods=['POST'])
# @app.route('/modem/start', methods=['POST'])
# @app.route('/modem/stop', methods=['POST'])

# @app.route('/rig/status', methods=['GET'])
# @app.route('/rig/mode', methods=['POST'])
# @app.route('/rig/frequency', methods=['POST'])
# @app.route('/rig/test_hamlib', methods=['POST'])

# Event websocket
@sock.route('/events')
def echo(sock):
        ev = app.modem_events.get()
        sock.send(ev)
