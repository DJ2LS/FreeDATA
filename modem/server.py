import sys
import os
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)


import time
from flask import Flask, request, jsonify, make_response, abort, Response
from flask_sock import Sock
from flask_cors import CORS
import serial_ports
from config import CONFIG
import audio
import queue
import service_manager
import state_manager
import json
import websocket_manager as wsm
import api_validations as validations
import command_cq
import command_beacon
import command_ping
import command_feq
import command_test
import command_arq_raw
import command_message_send
import event_manager
import atexit

from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_beacon import DatabaseManagerBeacon
from schedule_manager import ScheduleManager

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
sock = Sock(app)
MODEM_VERSION = "0.15.3-alpha"

# set config file to use
def set_config():
    if 'FREEDATA_CONFIG' in os.environ:
        config_file = os.environ['FREEDATA_CONFIG']
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, 'config.ini')

    if os.path.exists(config_file):
        print(f"Using config from {config_file}")
    else:
        print(f"Config file '{config_file}' not found. Exiting.")
        sys.exit(1)

    return config_file




# returns a standard API response
def api_response(data, status = 200):
    return make_response(jsonify(data), status)

def api_abort(message, code):
    jsonError = json.dumps({'error': message})
    abort(Response(jsonError, code))

def api_ok(message = "ok"):
    return api_response({'message': message})

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
    try:
        command = cmd_class(app.config_manager.read(), app.state_manager, app.event_manager,  params)
        app.logger.info(f"Command {command.get_name()} running...")
        if command.run(app.modem_events, app.service_manager.modem): # TODO remove the app.modem_event custom queue
            return True
    except Exception as e:
        app.logger.warning(f"Command {command.get_name()} failed...: {e}")
        return False

## REST API
@app.route('/', methods=['GET'])
def index():
    return api_response({'name': 'FreeDATA API',
                    'description': '',
                    'api_version': 1,
                    'modem_version': MODEM_VERSION,
                    'license': 'GPL3.0',
                    'documentation': 'https://wiki.freedata.app',
                    })

# get and set config
@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method in ['POST']:

        if not validations.validate_remote_config(request.json):
            return api_abort("wrong config", 500)
        # check if config already exists
        if app.config_manager.read() == request.json:
            return api_response(request.json)

        set_config = app.config_manager.write(request.json)
        if not set_config:
            response = api_response(None, 'error writing config')
        else:
            app.modem_service.put("restart")
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
    return api_ok()

@app.route('/modem/beacon', methods=['POST'])
def post_beacon():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for controlling BEACON STATE via POST"})
    if not isinstance(request.json['enabled'], bool) or not isinstance(request.json['away_from_key'], bool):
        api_abort(f"Incorrect value for 'enabled'. Shoud be bool.")
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)

    if not app.state_manager.is_beacon_running:
        app.state_manager.set('is_beacon_running', request.json['enabled'])
        app.state_manager.set('is_away_from_key', request.json['away_from_key'])

        if not app.state_manager.getARQ():
            enqueue_tx_command(command_beacon.BeaconCommand, request.json)
    else:
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
    return api_ok()

@app.route('/modem/send_test_frame', methods=['POST'])
def post_send_test_frame():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for triggering a TEST_FRAME via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    enqueue_tx_command(command_test.TestCommand)
    return api_ok()

@app.route('/modem/fec_transmit', methods=['POST'])
def post_send_fec_frame():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for triggering a FEC frame via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    enqueue_tx_command(command_feq.FecCommand, request.json)
    return api_ok()

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
    return api_ok()

@app.route('/version', methods=['GET'])
def get_modem_version():
    return api_response({"version": app.MODEM_VERSION})

@app.route('/modem/send_arq_raw', methods=['POST'])
def post_modem_send_raw():
    if request.method not in ['POST']:
        return api_response({"info": "endpoint for SENDING RAW DATA via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)
    if app.state_manager.check_if_running_arq_session():
        api_abort('Modem busy', 503)
    if enqueue_tx_command(command_arq_raw.ARQRawCommand, request.json):
        return api_response(request.json)
    else:
        api_abort('Error executing command...', 500)
@app.route('/modem/stop_transmission', methods=['POST'])
def post_modem_send_raw_stop():

    if request.method not in ['POST']:
        return api_response({"info": "endpoint for SENDING a STOP command via POST"})
    if not app.state_manager.is_modem_running:
        api_abort('Modem not running', 503)

    if app.state_manager.getARQ():
        for id in app.state_manager.arq_irs_sessions:
            app.state_manager.arq_irs_sessions[id].abort_transmission()
        for id in app.state_manager.arq_iss_sessions:
            app.state_manager.arq_iss_sessions[id].abort_transmission()

    return api_response(request.json)

@app.route('/radio', methods=['GET', 'POST'])
def get_post_radio():
    if request.method in ['POST']:
        if "radio_frequency" in request.json:
            app.radio_manager.set_frequency(request.json['radio_frequency'])
        if "radio_mode" in request.json:
            app.radio_manager.set_mode(request.json['radio_mode'])
        if "radio_rf_level" in request.json:
            app.radio_manager.set_rf_level(int(request.json['radio_rf_level']))

        return api_response(request.json)
    elif request.method == 'GET':
        return api_response(app.state_manager.get_radio_status())

@app.route('/freedata/messages', methods=['POST', 'GET'])
def get_post_freedata_message():
    if request.method in ['GET']:
        result = DatabaseManagerMessages(app.event_manager).get_all_messages_json()
        return api_response(result)
    if request.method in ['POST']:
        enqueue_tx_command(command_message_send.SendMessageCommand, request.json)
        return api_response(request.json)

    api_abort('Error executing command...', 500)

@app.route('/freedata/messages/<string:message_id>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def handle_freedata_message(message_id):
    if request.method == 'GET':
        message = DatabaseManagerMessages(app.event_manager).get_message_by_id_json(message_id)
        return message
    elif request.method == 'POST':
        result = DatabaseManagerMessages(app.event_manager).update_message(message_id, update_data={'status': 'queued'})
        DatabaseManagerMessages(app.event_manager).increment_message_attempts(message_id)
        return api_response(result)
    elif request.method == 'PATCH':
        # Fixme We need to adjust this
        result = DatabaseManagerMessages(app.event_manager).mark_message_as_read(message_id)
        return api_response(result)
    elif request.method == 'DELETE':
        result = DatabaseManagerMessages(app.event_manager).delete_message(message_id)
        return api_response(result)
    else:
        api_abort('Error executing command...', 500)

@app.route('/freedata/messages/<string:message_id>/attachments', methods=['GET'])
def get_message_attachments(message_id):
    attachments = DatabaseManagerAttachments(app.event_manager).get_attachments_by_message_id_json(message_id)
    return api_response(attachments)

@app.route('/freedata/messages/attachment/<string:data_sha512>', methods=['GET'])
def get_message_attachment(data_sha512):
    attachment = DatabaseManagerAttachments(app.event_manager).get_attachment_by_sha512(data_sha512)
    return api_response(attachment)

@app.route('/freedata/beacons', methods=['GET'])
def get_all_beacons():
    beacons = DatabaseManagerBeacon(app.event_manager).get_all_beacons()
    return api_response(beacons)

@app.route('/freedata/beacons/<string:callsign>', methods=['GET'])
def get_beacons_by_callsign(callsign):
    beacons = DatabaseManagerBeacon(app.event_manager).get_beacons_by_callsign(callsign)
    return api_response(beacons)

# Event websocket
@sock.route('/events')
def sock_events(sock):
    wsm.handle_connection(sock, wsm.events_client_list, app.modem_events) # TODO remove the app.modem_event custom queue

@sock.route('/fft')
def sock_fft(sock):
    wsm.handle_connection(sock, wsm.fft_client_list, app.modem_fft)

@sock.route('/states')
def sock_states(sock):
    wsm.handle_connection(sock, wsm.states_client_list, app.state_queue)

@atexit.register
def stop_server():
    print("------------------------------------------")
    try:
        app.service_manager.modem_service.put("stop")
        if app.socket_interface_manager:
            app.socket_interface_manager.stop_servers()

        if app.service_manager.modem:
            app.service_manager.modem.sd_input_stream.stop
        audio.sd._terminate()
    except Exception as e:
        print(e)
        print("Error stopping modem")
    time.sleep(1)
    print('Server shutdown...')
    print("------------------------------------------")

def main():
    app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 10}
    # define global MODEM_VERSION
    app.MODEM_VERSION = MODEM_VERSION

    config_file = set_config()
    app.config_manager = CONFIG(config_file)

    # start modem
    app.p2p_data_queue = queue.Queue() # queue which holds processing data of p2p connections
    app.state_queue = queue.Queue()  # queue which holds latest states
    app.modem_events = queue.Queue()  # queue which holds latest events
    app.modem_fft = queue.Queue()  # queue which holds latest fft data
    app.modem_service = queue.Queue()  # start / stop modem service
    app.event_manager = event_manager.EventManager([app.modem_events])  # TODO remove the app.modem_event custom queue
    # init state manager
    app.state_manager = state_manager.StateManager(app.state_queue)
    # initialize message system schedule manager
    app.schedule_manager = ScheduleManager(app.MODEM_VERSION, app.config_manager, app.state_manager, app.event_manager)
    # start service manager
    app.service_manager = service_manager.SM(app)

    # start modem service
    app.modem_service.put("start")
    # initialize database default values
    DatabaseManager(app.event_manager).initialize_default_values()
    wsm.startThreads(app)

    conf = app.config_manager.read()
    modemaddress = conf['NETWORK']['modemaddress']
    modemport = conf['NETWORK']['modemport']

    if not modemaddress:
        modemaddress = '127.0.0.1'
    if not modemport:
        modemport = 5000

    app.run(modemaddress, modemport)

if __name__ == "__main__":
    main()