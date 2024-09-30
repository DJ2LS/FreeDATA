import os
import sys
# we need to add script directory to the sys path for avoiding problems with pip package
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)

import signal
import queue
import asyncio
import webbrowser
import platform
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import threading
import serial_ports
from config import CONFIG
import audio
import service_manager
import state_manager
import websocket_manager
import api_validations as validations
import command_cq
import command_beacon
import command_ping
import command_feq
import command_test
import command_arq_raw
import command_message_send
import event_manager
import structlog
from log_handler import setup_logging
import adif_udp_logger

from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_beacon import DatabaseManagerBeacon
from message_system_db_station import DatabaseManagerStations
from schedule_manager import ScheduleManager

# Constants
CONFIG_ENV_VAR = 'FREEDATA_CONFIG'
DEFAULT_CONFIG_FILE = 'config.ini'

MODEM_VERSION = "0.16.7-alpha"

API_VERSION = 3
LICENSE = 'GPL3.0'
DOCUMENTATION_URL = 'https://wiki.freedata.app'

# adjust asyncio for windows usage for avoiding a Assertion Error
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    #print("startup")
    yield
    stop_server()

app = FastAPI(lifespan=lifespan)

# custom logger for fastapi
#setup_logging()
logger = structlog.get_logger()

potential_gui_dirs = [
    "../freedata_gui/dist", # running server with "python3 server.py
    "freedata_gui/dist", # running sever with ./tools/run-server.py
    "FreeDATA/freedata_gui/dist", # running server with bash run-server...
    os.path.join(os.path.dirname(__file__), "gui") # running server as nuitka bundle
]

# Check which directory exists and set gui_dir accordingly
gui_dir = None
for dir_path in potential_gui_dirs:
    if os.path.isdir(dir_path):
        gui_dir = dir_path
        break

# Configure app to serve static files if gui_dir is found
if gui_dir:
    app.mount("/gui", StaticFiles(directory=gui_dir, html=True), name="static")
else:
    logger.warning("GUI directory not found. Please run `npm i && npm run build` inside `freedata_gui`.")



@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"[API] {request.method}", url=str(request.url), response_code=response.status_code)
    return response


# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Returns a standard API response
def api_response(data, status=200):
    return JSONResponse(content=data, status_code=status)


def api_abort(message, code):
    raise HTTPException(status_code=code, detail={"error": message})


def api_ok(message="ok"):
    return api_response({'message': message})


# Validates a parameter
def validate(req, param, validator, is_required=True):
    if param not in req:
        if is_required:
            api_abort(f"Required parameter '{param}' is missing.", 400)
        else:
            return True
    if not validator(req[param]):
        api_abort(f"Value of '{param}' is invalid.", 400)


# Set config file to use
def set_config():
    config_file = os.getenv(CONFIG_ENV_VAR, os.path.join(script_directory, DEFAULT_CONFIG_FILE))
    if os.path.exists(config_file):
        print(f"Using config from {config_file}")
    else:
        print(f"Config file '{config_file}' not found. Exiting.")
        sys.exit(1)
    return config_file


# Enqueue a transmit command
async def enqueue_tx_command(cmd_class, params={}):
    try:
        command = cmd_class(app.config_manager.read(), app.state_manager, app.event_manager, params)
        print(f"Command {command.get_name()} running...")

        # Run the command in a separate thread to avoid blocking
        result = await asyncio.to_thread(command.run, app.modem_events, app.service_manager.modem)  # TODO: remove the app.modem_event custom queue

        if result:
            return True
    except Exception as e:
        print(f"Command failed: {e}")
    return False

# API Endpoints
@app.get("/")
async def index():

    return {
        'name': 'FreeDATA API',
        'description': 'A sample API that provides free data services',
        'api_version': API_VERSION,
        'modem_version': MODEM_VERSION,
        'license': LICENSE,
        'documentation': DOCUMENTATION_URL,
    }

@app.get("/config")
async def get_config():
    return app.config_manager.read()

@app.post("/config")
async def post_config(request: Request):
    config = await request.json()
    print(config)
    if not validations.validate_remote_config(config):
        api_abort("Invalid config", 400)
    if app.config_manager.read() == config:
        return config
    set_config = app.config_manager.write(config)
    if not set_config:
        api_abort("Error writing config", 500)
    app.modem_service.put("restart")
    return set_config

@app.get("/devices/audio")
async def get_audio_devices():
    #dev_in, dev_out = audio.get_audio_devices()
    dev_in, dev_out = audio.fetch_audio_devices([], [])

    return {'in': dev_in, 'out': dev_out}

@app.get("/devices/serial")
async def get_serial_devices():
    devices = serial_ports.get_ports()
    return devices

@app.get("/modem/state")
async def get_modem_state():
    return app.state_manager.sendState()

@app.post("/modem/cqcqcq")
async def post_cqcqcq():
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(command_cq.CQCommand)
    return api_ok()

@app.post("/modem/beacon")
async def post_beacon(request: Request):
    data = await request.json()
    if not isinstance(data.get('enabled'), bool) or not isinstance(data.get('away_from_key'), bool):
        api_abort("Incorrect value for 'enabled' or 'away_from_key'. Should be bool.", 400)
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    app.state_manager.set('is_beacon_running', data['enabled'])
    app.state_manager.set('is_away_from_key', data['away_from_key'])
    if not app.state_manager.getARQ() and data['enabled']:
        await enqueue_tx_command(command_beacon.BeaconCommand, data)
    return api_ok()

@app.post("/modem/ping_ping")
async def post_ping(request: Request):
    data = await request.json()
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    validate(data, 'dxcall', validations.validate_freedata_callsign)
    await enqueue_tx_command(command_ping.PingCommand, data)
    return api_ok()

@app.post("/modem/send_test_frame")
async def post_send_test_frame():
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(command_test.TestCommand)
    return api_ok()

@app.post("/modem/fec_transmit")
async def post_send_fec_frame(request: Request):
    data = await request.json()
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(command_feq.FecCommand, data)
    return api_ok()

@app.post("/modem/fec_is_writing")
async def post_send_fec_is_writing():
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    return {"info": "Not implemented yet"}

@app.post("/modem/start")
async def post_modem_start():
    app.modem_service.put("start")
    return api_ok()

@app.post("/modem/stop")
async def post_modem_stop():
    app.modem_service.put("stop")
    return api_ok()

@app.get("/version")
async def get_modem_version():
    os_info = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
    }

    python_info = {
        'build': platform.python_build(),
        'compiler': platform.python_compiler(),
        'branch': platform.python_branch(),
        'implementation': platform.python_implementation(),
        'revision': platform.python_revision(),
        'version': platform.python_version()
    }

    return {
        'api_version': API_VERSION,
        'modem_version': MODEM_VERSION,
        'os_info': os_info,
        'python_info': python_info
    }

@app.post("/modem/send_arq_raw")
async def post_modem_send_raw(request: Request):
    data = await request.json()
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    if app.state_manager.check_if_running_arq_session():
        api_abort("Modem busy", 503)
    if await enqueue_tx_command(command_arq_raw.ARQRawCommand, data):
        return api_response(data)
    api_abort("Error executing command", 500)

@app.post("/modem/stop_transmission")
async def post_modem_send_raw_stop():
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    if app.state_manager.getARQ():
        try:
            for session in app.state_manager.arq_irs_sessions.values():
                #session.abort_transmission()
                session.transmission_aborted()
            for session in app.state_manager.arq_iss_sessions.values():
                session.abort_transmission(send_stop=False)
                session.transmission_aborted()
        except Exception as e:
            print(f"Error during transmission stopping: {e}")
    return api_ok()

@app.get("/radio")
async def get_radio():
    return app.state_manager.get_radio_status()

@app.post("/radio")
async def post_radio(request: Request):
    data = await request.json()
    radio_manager = app.radio_manager
    if "radio_frequency" in data:
        radio_manager.set_frequency(data['radio_frequency'])
    if "radio_mode" in data:
        radio_manager.set_mode(data['radio_mode'])
    if "radio_rf_level" in data:
        radio_manager.set_rf_level(int(data['radio_rf_level']))
    if "radio_tuner" in data:
        radio_manager.set_tuner(data['radio_tuner'])
    return api_response(data)

@app.get("/freedata/messages")
async def get_freedata_messages(request: Request):
    filters = {k: v for k, v in request.query_params.items() if v}
    result = DatabaseManagerMessages(app.event_manager).get_all_messages_json(filters=filters)
    return api_response(result)

@app.post("/freedata/messages")
async def post_freedata_message(request: Request):
    data = await request.json()
    await enqueue_tx_command(command_message_send.SendMessageCommand, data)
    return api_response(data)

@app.post("/freedata/messages/{message_id}/adif")
async def post_freedata_message_adif_log(message_id: str):
    adif_output = DatabaseManagerMessages(app.event_manager).get_message_by_id_adif(message_id)
    # Send the ADIF data via UDP
    adif_udp_logger.send_adif_qso_data(app.config_manager.read(), adif_output)
    return api_response(adif_output)

@app.get("/freedata/messages/{message_id}")
async def get_freedata_message(message_id: str):
    message = DatabaseManagerMessages(app.event_manager).get_message_by_id_json(message_id)
    return api_response(message)

@app.patch("/freedata/messages/{message_id}")
async def patch_freedata_message(message_id: str, request: Request):
    data = await request.json()

    if data.get("action") == "retransmit":
        result = DatabaseManagerMessages(app.event_manager).update_message(message_id, update_data={'status': 'queued'})
        DatabaseManagerMessages(app.event_manager).increment_message_attempts(message_id)
    else:
        result = DatabaseManagerMessages(app.event_manager).update_message(message_id, update_data=data)

    return api_response(result)

@app.delete("/freedata/messages/{message_id}")
async def delete_freedata_message(message_id: str):
    result = DatabaseManagerMessages(app.event_manager).delete_message(message_id)
    return api_response(result)

@app.get("/freedata/messages/{message_id}/attachments")
async def get_message_attachments(message_id: str):
    attachments = DatabaseManagerAttachments(app.event_manager).get_attachments_by_message_id_json(message_id)
    return api_response(attachments)

@app.get("/freedata/messages/attachment/{data_sha512}")
async def get_message_attachment(data_sha512: str):
    attachment = DatabaseManagerAttachments(app.event_manager).get_attachment_by_sha512(data_sha512)
    return api_response(attachment)

@app.get("/freedata/beacons")
async def get_all_beacons():
    beacons = DatabaseManagerBeacon(app.event_manager).get_all_beacons()
    return api_response(beacons)

@app.get("/freedata/beacons/{callsign}")
async def get_beacons_by_callsign(callsign: str):
    beacons = DatabaseManagerBeacon(app.event_manager).get_beacons_by_callsign(callsign)
    return api_response(beacons)

@app.get("/freedata/station/{callsign}")
async def get_station_info(callsign: str):
    station = DatabaseManagerStations(app.event_manager).get_station(callsign)
    return api_response(station)

@app.post("/freedata/station/{callsign}")
async def set_station_info(callsign: str, request: Request):
    data = await request.json()
    result = DatabaseManagerStations(app.event_manager).update_station_info(callsign, new_info=data["info"])
    return api_response(result)

# WebSocket Event Handlers
@app.websocket("/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    await app.wsm.handle_connection(websocket, app.wsm.events_client_list, app.modem_events)

@app.websocket("/fft")
async def websocket_fft(websocket: WebSocket):
    await websocket.accept()
    await app.wsm.handle_connection(websocket, app.wsm.fft_client_list, app.modem_fft)

@app.websocket("/states")
async def websocket_states(websocket: WebSocket):
    await websocket.accept()
    await app.wsm.handle_connection(websocket, app.wsm.states_client_list, app.state_queue)

# Signal Handler
def signal_handler(sig, frame):
    print("\n------------------------------------------")
    logger.warning("[SHUTDOWN] Received SIGINT....")
    stop_server()

def stop_server():
    # INFO attempt stopping ongoing transmission for reducing chance of stuck PTT
    if hasattr(app, 'state_manager'):
        logger.warning("[SHUTDOWN] stopping ongoing transmissions....")
        try:
            for session in app.state_manager.arq_irs_sessions.values():
                #session.abort_transmission()
                session.transmission_aborted()
            for session in app.state_manager.arq_iss_sessions.values():
                session.abort_transmission(send_stop=False)
                session.transmission_aborted()
        except Exception as e:
            print(f"Error during transmission stopping: {e}")

    if hasattr(app, 'wsm'):
        app.wsm.shutdown()
    if hasattr(app, 'radio_manager'):
        app.radio_manager.stop()
    if hasattr(app, 'schedule_manager'):
        app.schedule_manager.stop()
    if hasattr(app.service_manager, 'modem_service') and app.service_manager.modem_service:
        app.service_manager.shutdown()
    if hasattr(app.service_manager, 'modem') and app.service_manager.modem:
        app.service_manager.modem.demodulator.shutdown()
    if hasattr(app.service_manager, 'modem_service'):
        app.service_manager.stop_modem()
    if hasattr(app, 'socket_interface_manager') and app.socket_interface_manager:
        app.socket_interface_manager.stop_servers()
    if hasattr(app, 'socket_interface_manager') and app.socket_interface_manager:
        app.socket_interface_manager.stop_servers()
    audio.terminate()
    logger.warning("[SHUTDOWN] Shutdown completed")
    try:
        # it seems sys.exit causes problems since we are using fastapi
        # fastapi seems to close the application
        #sys.exit(0)
        os._exit(0)

        pass
    except Exception as e:
        logger.warning("[SHUTDOWN] Shutdown completed", error=e)


def open_browser_after_delay(url, delay=2):
    threading.Event().wait(delay)
    webbrowser.open(url, new=0, autoraise=True)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    app.MODEM_VERSION = MODEM_VERSION
    config_file = set_config()
    app.config_manager = CONFIG(config_file)
    app.p2p_data_queue = queue.Queue()
    app.state_queue = queue.Queue()
    app.modem_events = queue.Queue()
    app.modem_fft = queue.Queue()
    app.modem_service = queue.Queue()
    app.event_manager = event_manager.EventManager([app.modem_events])
    app.state_manager = state_manager.StateManager(app.state_queue)
    app.schedule_manager = ScheduleManager(app.MODEM_VERSION, app.config_manager, app.state_manager, app.event_manager)
    app.service_manager = service_manager.SM(app)
    app.modem_service.put("start")
    DatabaseManager(app.event_manager).initialize_default_values()
    DatabaseManager(app.event_manager).database_repair_and_cleanup()
    app.wsm = websocket_manager.wsm()
    app.wsm.startWorkerThreads(app)

    conf = app.config_manager.read()
    modemaddress = conf['NETWORK'].get('modemaddress', '127.0.0.1')
    modemport = int(conf['NETWORK'].get('modemport', 5000))

    # check if modemadress is empty - known bug caused by older versions
    if modemaddress in ['', None]:
        modemaddress = '127.0.0.1'

    if gui_dir and os.path.isdir(gui_dir):
        url = f"http://{modemaddress}:{modemport}/gui"

        logger.info("---------------------------------------------------")
        logger.info("                                                   ")
        logger.info(f"[GUI] AVAILABLE ON {url}")
        logger.info("just open it in your browser")
        logger.info("                                                   ")
        logger.info("---------------------------------------------------")

        if conf['GUI'].get('auto_run_browser', True):
            threading.Thread(target=open_browser_after_delay, args=(url, 2)).start()


    uvicorn.run(app, host=modemaddress, port=modemport, log_config=None, log_level="info")


if __name__ == "__main__":
    main()
