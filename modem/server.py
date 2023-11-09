from flask import Flask, request, jsonify, make_response
from flask_sock import Sock
from flask_cors import CORS
import os
import serial_ports
from config import CONFIG
import audio
import data_handler
import modem
import queue
import server_commands

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
def api_response(data):
    return make_response(jsonify(data), 200)

set_config()

# start modem
app.modem_events = queue.Queue()
app.modem_fft = queue.Queue()

app.modem = modem.RF(app.config_manager.config, app.modem_events, app.modem_fft)
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

@app.route('/modem/cqcqcq', methods=['POST', 'GET'])
def post_cqcqcq():
    if request.method in ['POST']:
        server_commands.cqcqcq()
        return api_response({"cmd": "cqcqcq"})
    else:
        return api_response({"info": "endpoint for triggering a CQ via POST"})

@app.route('/modem/beacon', methods=['POST'])
def post_beacon():
    if request.method in ['POST']:
        server_commands.beacon(request.json)
        return api_response(request.json)
    else:
        return api_response({"info": "endpoint for controlling BEACON STATE via POST"})

@app.route('/modem/ping_ping', methods=['POST'])
def post_ping():
    if request.method in ['POST']:
        server_commands.ping_ping(request.json)
        return api_response(request.json)
    else:
        return api_response({"info": "endpoint for controlling PING via POST"})

# @app.route('/modem/listen', methods=['POST']) # not needed if we are restarting modem on changing settings
# @app.route('/modem/record_audio', methods=['POST'])
# @app.route('/modem/responde_to_call', methods=['POST']) # not needed if we are restarting modem on changing settings
# @app.route('/modem/responde_to_cq', methods=['POST']) # not needed if we are restarting modem on changing settings
# @app.route('/modem/audio_levels', methods=['POST']) # tx and rx # not needed if we are restarting modem on changing settings
# @app.route('/modem/send_test_frame', methods=['POST'])
# @app.route('/modem/fec_transmit', methods=['POST'])
# @app.route('/modem/fec_is_writing', methods=['POST'])

# @app.route('/modem/mesh_ping', methods=['POST'])
# @app.route('/modem/arq_connect', methods=['POST'])
# @app.route('/modem/arq_disconnect', methods=['POST'])
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


# our client set which contains all connected websocket clients
client_list = set()
# our transmit function which also handles client management
def transmit_sock_data(data):
    try:
        for client in client_list:
            try:
                client.send(data)
            except Exception:
                # print("client not connected anymore")
                client_list.remove(client)
    except RuntimeError:
        # print("set changed during iteration")
        pass

# Event websocket
@sock.route('/events')
def sock_events(sock):
    # it seems we have to keep the logics inside a loop, otherwise connection will be terminated
    client_list.add(sock)
    while True:
        ev = app.modem_events.get()
        transmit_sock_data(ev)

# FFT Websocket
@sock.route('/fft')
def sock_fft(sock):
    # it seems we have to keep the logics inside a loop, otherwise connection will be terminated
    client_list.add(sock)
    while True:
        fft = app.modem_fft.get()
        transmit_sock_data(fft)
