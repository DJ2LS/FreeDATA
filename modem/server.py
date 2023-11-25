from flask import Flask, request, jsonify, make_response, abort, Response
from flask_sock import Sock
from flask_cors import CORS
import os
import serial_ports
from config import CONFIG
import audio
import queue
import service_manager
import state_manager
import ujson as json
import websocket_manager as wsm
import api_validations as validations
import command_ping
import command_cq
import command_ping
import command_feq
import command_test
from queues import DATA_QUEUE_TRANSMIT as tx_cmd_queue

app = Flask(__name__)
CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})
sock = Sock(app)
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 10}

# define global MODEM_VERSION
app.MODEM_VERSION = "0.12.0-alpha"

# set config file to use
def set_config():
    if 'FREEDATA_CONFIG' in os.environ:
        config_file = os.environ['FREEDATA_CONFIG']
    else:
        config_file = 'config.ini'

    if os.path.exists(config_file):
        print(f"Using config from {config_file}")
    else:
        print(f"Config file '{config_file}' not found. Exiting.")
        exit(1)

    app.config_manager = CONFIG(config_file)

set_config()

# start modem
app.state_queue = queue.Queue() # queue which holds latest states
app.modem_events = queue.Queue() # queue which holds latest events
app.modem_fft = queue.Queue() # queue which holds latest fft data
app.modem_service = queue.Queue() # start / stop modem service

# init state manager
app.state_manager = state_manager.StateManager(app.state_queue)

# start service manager
service_manager.SM(app)

# start modem service
app.modem_service.put("start")

# returns a standard API response
def api_response(data, status = 200):
    return make_response(jsonify(data), status)

def api_abort(message, code):
    jsonError = json.dumps({'error': message})
    abort(Response(jsonError, code))

# validates a parameter
def validate(req, param, validator, isRequired = True):
    if param not in req:
        if isRequired:
            api_abort(f"Required parameter '{param}' is missing.", 400)
        else:
            return True
    if not validator(req[param]):
        api_abort(f"Value of '{param}' is invalid.", 400)

# Takes a transmit command and puts it in the transmit command queue
def enqueue_tx_command(cmd_class, params = {}):
    command = cmd_class(app.config, app.logger, params)
    tx_cmd_queue.put(command)
    app.logger.info(f"Command {command.get_name()} enqueued.")

## REST API
@app.route('/', methods=['GET'])
def index():
    return api_response({'name': 'FreeDATA API',
                    'description': '',
                    'api_version': 1,
                    'modem_version': app.MODEM_VERSION,
                    'license': 'GPL3.0',
                    'documentation': 'https://wiki.freedata.app',
                    })

# get and set config
@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method in ['POST']:
        set_config = app.config_manager.write(request.json)
        app.modem_service.put("restart")
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

@app.route('/modem/state', methods=['GET'])
def get_modem_state():
    return api_response(app.state_manager.sendState())

@app.route('/modem/cqcqcq', methods=['POST', 'GET'])
def post_cqcqcq():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for triggering a CQ via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    enqueue_tx_command(command_cq.CQCommand)
    return "ok"

@app.route('/modem/beacon', methods=['POST'])
def post_beacon():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for controlling BEACON STATE via POST"})
    if not isinstance(request.json['enabled'], bool):
        api_abort(f"Incorrect value for 'enabled'. Shoud be bool.")
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    app.state_manager.set('is_beacon_running', request.json['enabled'])
    return api_response(request.json)

@app.route('/modem/ping_ping', methods=['POST'])
def post_ping():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for controlling PING via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    validate(request.json, 'dxcall', validations.validate_freedata_callsign)
    enqueue_tx_command(command_ping.PingCommand, request.json)
    return 'ok'

@app.route('/modem/send_test_frame', methods=['POST'])
def post_send_test_frame():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for triggering a TEST_FRAME via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    enqueue_tx_command(command_test.TestCommand)
    return "ok"

@app.route('/modem/fec_transmit', methods=['POST'])
def post_send_fec_frame():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for triggering a FEC frame via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    enqueue_tx_command(command_feq.FecCommand, request.json)
    return "ok"

@app.route('/modem/fec_is_writing', methods=['POST'])
def post_send_fec_is_writing():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for triggering a IS WRITING frame via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    #server_commands.modem_fec_is_writing(request.json)
    return 'Not implemented yet'

@app.route('/modem/start', methods=['POST'])
def post_modem_start():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for STARTING modem via POST"})
    print("start received...")
    app.modem_service.put("start")
    return api_response(request.json)

@app.route('/modem/stop', methods=['POST'])
def post_modem_stop():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for STOPPING modem via POST"})
    print("stop received...")

    app.modem_service.put("stop")
    return api_response(request.json)

@app.route('/version', methods=['GET'])
def get_modem_version():
    return api_response({"version": app.MODEM_VERSION})

@app.route('/modem/send_arq_raw', methods=['POST'])
def post_modem_send_raw():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for SENDING RAW DATA via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)

    # server_commands.modem_arq_send_raw(request.json)
    return "Not implemented yet"

# @app.route('/modem/arq_connect', methods=['POST'])
# @app.route('/modem/arq_disconnect', methods=['POST'])
# @app.route('/modem/send_raw', methods=['POST'])
# @app.route('/modem/stop_transmission', methods=['POST'])
# @app.route('/modem/listen', methods=['POST']) # not needed if we are restarting modem on changing settings
# @app.route('/modem/record_audio', methods=['POST'])
# @app.route('/modem/responde_to_call', methods=['POST']) # not needed if we are restarting modem on changing settings
# @app.route('/modem/responde_to_cq', methods=['POST']) # not needed if we are restarting modem on changing settings
# @app.route('/modem/audio_levels', methods=['POST']) # tx and rx # not needed if we are restarting modem on changing settings
# @app.route('/modem/mesh_ping', methods=['POST'])
# @app.route('/mesh/routing_table', methods=['GET'])
# @app.route('/modem/get_rx_buffer', methods=['GET'])
# @app.route('/modem/del_rx_buffer', methods=['POST'])
# @app.route('/rig/status', methods=['GET'])
# @app.route('/rig/mode', methods=['POST'])
# @app.route('/rig/frequency', methods=['POST'])
# @app.route('/rig/test_hamlib', methods=['POST'])

# Event websocket
@sock.route('/events')
def sock_events(sock):
    wsm.handle_connection(sock, wsm.events_client_list, app.modem_events)

@sock.route('/fft')
def sock_fft(sock):
    if len(wsm.fft_client_list) == 0:
        app.modem_service.put("fft:true")
        print("Streaming data to FFT socket since a client is connected")
    wsm.handle_connection(sock, wsm.fft_client_list, app.modem_fft)

@sock.route('/states')
def sock_states(sock):
    wsm.handle_connection(sock, wsm.states_client_list, app.state_queue)

wsm.startThreads(app)