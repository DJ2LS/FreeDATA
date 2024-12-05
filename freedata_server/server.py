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
import command_transmit_sine
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

MODEM_VERSION = "0.16.10-alpha"

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
@app.get("/", summary="API Root", tags=["General"], responses={
    200: {
        "description": "API information.",
        "content": {
            "application/json": {
                "example": {
                    "name": "FreeDATA API",
                    "description": "A sample API that provides free data services",
                    "api_version": 3,
                    "modem_version": "0.16.8-alpha",
                    "license": "GPL3.0",
                    "documentation": "https://wiki.freedata.app"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Service unavailable.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Service unavailable."
                }
            }
        }
    }
})
async def index():
    """
    Retrieve API metadata.

    Returns:
        dict: A JSON object containing API metadata.
    """
    return {
        'name': 'FreeDATA API',
        'description': 'A sample API that provides free data services',
        'api_version': 3,
        'modem_version': "0.16.8-alpha",
        'license': "GPL3.0",
        'documentation': "https://wiki.freedata.app",
    }


@app.get("/config", summary="Get Modem Configuration", tags=["Configuration"], responses={
    200: {
        "description": "Current modem configuration settings.",
        "content": {
            "application/json": {
                "example": {
                    "AUDIO": {
                        "input_device": "2fc0",
                        "output_device": "3655",
                        "rx_audio_level": 0,
                        "tx_audio_level": 2
                    },
                    "MESH": {
                        "enable_protocol": False
                    },
                    "MESSAGES": {
                        "enable_auto_repeat": True
                    },
                    "MODEM": {
                        "enable_hmac": False,
                        "enable_morse_identifier": False,
                        "enable_socket_interface": False,
                        "maximum_bandwidth": 2438,
                        "tx_delay": 200
                    },
                    "NETWORK": {
                        "modemaddress": "",
                        "modemport": 5000
                    },
                    "RADIO": {
                        "control": "rigctld",
                        "data_bits": 8,
                        "model_id": 1001,
                        "ptt_port": "ignore",
                        "ptt_type": "USB",
                        "serial_dcd": "NONE",
                        "serial_dtr": "OFF",
                        "serial_handshake": "ignore",
                        "serial_port": "/dev/cu.Bluetooth-Incoming-Port",
                        "serial_speed": 38400,
                        "stop_bits": 1
                    },
                    "RIGCTLD": {
                        "arguments": "",
                        "command": "",
                        "ip": "127.0.0.1",
                        "path": "",
                        "port": 4532
                    },
                    "SOCKET_INTERFACE": {
                        "cmd_port": 0,
                        "data_port": 0,
                        "enable": False,
                        "host": ""
                    },
                    "STATION": {
                        "enable_explorer": True,
                        "enable_stats": True,
                        "mycall": "LA3QMA",
                        "mygrid": "JP20ql",
                        "myssid": 0,
                        "ssid_list": [0,1,2,3,4,5,6,7,8,9],
                        "respond_to_cq": True,
                    },
                    "TCI": {
                        "tci_ip": "127.0.0.1",
                        "tci_port": 50001
                    }
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def get_config():
    """
    Retrieve the current modem configuration.

    Returns:
        dict: The modem configuration settings.
    """
    return app.config_manager.read()


@app.post("/config", summary="Update Modem Configuration", tags=["Configuration"], responses={
    200: {
        "description": "Modem configuration updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "AUDIO": {
                        "input_device": "2fc0",
                        "output_device": "3655",
                        "rx_audio_level": 0,
                        "tx_audio_level": 2
                    },
                    # ... (rest of the configuration as in the GET example)
                }
            }
        }
    },
    400: {
        "description": "Invalid configuration data.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid config"
                }
            }
        }
    },
    500: {
        "description": "Error writing configuration.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Error writing config"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def post_config(request: Request):
    """
    Update the modem configuration with new settings.

    Parameters:
        request (Request): The HTTP request containing the new configuration in JSON format.

    Returns:
        dict: The updated modem configuration.

    Raises:
        HTTPException: If the provided configuration is invalid or an error occurs while writing the config.
    """
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


@app.get("/devices/audio", summary="Get Audio Devices", tags=["Devices"], responses={
    200: {
        "description": "List of available audio input and output devices.",
        "content": {
            "application/json": {
                "example": {
                    "in": [
                        {
                            "api": "ALSA",
                            "id": "8eb1",
                            "name": "pipewire",
                            "native_index": 4
                        },
                        {
                            "api": "ALSA",
                            "id": "8e7a",
                            "name": "default",
                            "native_index": 5
                        }
                    ],
                    "out": [
                        {
                            "api": "ALSA",
                            "id": "ae79",
                            "name": "HDA Intel HDMI: 0 (hw:0,3)",
                            "native_index": 0
                        },
                        {
                            "api": "ALSA",
                            "id": "67fd",
                            "name": "HDA Intel HDMI: 1 (hw:0,7)",
                            "native_index": 1
                        },
                        {
                            "api": "ALSA",
                            "id": "b68c",
                            "name": "HDA Intel HDMI: 2 (hw:0,8)",
                            "native_index": 2
                        },
                        {
                            "api": "ALSA",
                            "id": "ba84",
                            "name": "hdmi",
                            "native_index": 3
                        },
                        {
                            "api": "ALSA",
                            "id": "8eb1",
                            "name": "pipewire",
                            "native_index": 4
                        },
                        {
                            "api": "ALSA",
                            "id": "8e7a",
                            "name": "default",
                            "native_index": 5
                        }
                    ]
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_audio_devices():
    """
    Retrieve a list of available audio input and output devices.

    Returns:
        dict: A JSON object containing lists of input and output audio devices.
    """
    # Uncomment the following line if using the actual function
    # dev_in, dev_out = audio.get_audio_devices()
    dev_in, dev_out = audio.fetch_audio_devices([], [])
    return {'in': dev_in, 'out': dev_out}


@app.get("/devices/serial", summary="Get Serial Devices", tags=["Devices"], responses={
    200: {
        "description": "List of available serial devices (COM ports).",
        "content": {
            "application/json": {
                "example": [
                    {
                        "description": "n/a [26a9]",
                        "port": "/dev/ttyS4"
                    }
                ]
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_serial_devices():
    """
    Retrieve a list of available serial devices (COM ports).

    Returns:
        list: A list of dictionaries containing serial port information.
    """
    devices = serial_ports.get_ports()
    return devices


@app.get("/modem/state", summary="Get Modem State", tags=["Modem"], responses={
    200: {
        "description": "Current modem state information.",
        "content": {
            "application/json": {
                "example": {
                    "activities": {
                        "161dd75ef3b5847a": {
                            "activity_type": "ARQ_BURST_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": 4,
                            "timestamp": 1713034266
                        },
                        "168e90799d13b7b4": {
                            "activity_type": "ARQ_SESSION_INFO_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": -3,
                            "timestamp": 1713034248
                        },
                        "2218b849e937d36d": {
                            "activity_type": "QRV",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "gridsquare": "JP15OW",
                            "origin": "SOMECALL-1",
                            "snr": 2,
                            "timestamp": 1713034200
                        },
                        "3fb424827f4632ab": {
                            "activity_type": "BEACON",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "gridsquare": "JP22AI",
                            "origin": "CALLSIGN-1",
                            "snr": -8,
                            "timestamp": 1713034455
                        },
                        "743222d1dd64ce9d": {
                            "activity_type": "ARQ_SESSION_OPEN_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "origin": "CALL-1",
                            "session_id": 105,
                            "snr": -2,
                            "timestamp": 1713034243
                        },
                        "7589edf6bf23ceed": {
                            "activity_type": "ARQ_BURST_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": 2,
                            "timestamp": 1713034275
                        },
                        "9d2c5a98fe0f9894": {
                            "activity_type": "QRV",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "gridsquare": "JP12AW",
                            "origin": "CALLME-1",
                            "snr": 5,
                            "timestamp": 1713034178
                        },
                        "f85609dced4ea40a": {
                            "activity_type": "ARQ_BURST_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": 0,
                            "timestamp": 1713034257
                        }
                    },
                    "audio_dbfs": -7.915304862713354,
                    "channel_busy_slot": [False, False, True, False, False],
                    "is_away_from_key": False,
                    "is_beacon_running": True,
                    "is_modem_busy": False,
                    "is_modem_running": True,
                    "radio_frequency": "14093000",
                    "radio_mode": "PKTUSB",
                    "radio_status": True,
                    "s_meter_strength": "20",
                    "type": "state"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def get_modem_state():
    """
    Retrieve the current state of the modem.

    Returns:
        dict: A JSON object containing modem state information.
    """
    return app.state_manager.sendState()


@app.post("/modem/cqcqcq", summary="Send CQ Command", tags=["Modem"], responses={
    200: {
        "description": "CQ command sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "ok"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_cqcqcq():
    """
    Trigger the modem to send a CQ.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running.
    """
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(command_cq.CQCommand)
    return api_ok()


@app.post("/modem/beacon", summary="Enable/Disable Modem Beacon", tags=["Modem"], responses={
    200: {
        "description": "Beacon status updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "enabled": True,
                    "away_from_key": False
                }
            }
        }
    },
    400: {
        "description": "Invalid input parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Incorrect value for 'enabled' or 'away_from_key'. Should be bool."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_beacon(request: Request):
    """
    Enable or disable the modem beacon.

    Parameters:
        request (Request): The HTTP request containing the following JSON keys:
            - 'enabled' (bool): True to enable the beacon, False to disable.
            - 'away_from_key' (bool): True if away from key, False otherwise.

    Returns:
        dict: A JSON object indicating the beacon status.

    Raises:
        HTTPException: If parameters are invalid or modem is not running.
    """
    data = await request.json()
    if not isinstance(data.get('enabled'), bool) or not isinstance(data.get('away_from_key'), bool):
        api_abort("Incorrect value for 'enabled' or 'away_from_key'. Should be bool.", 400)
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    app.state_manager.set('is_beacon_running', data['enabled'])
    app.state_manager.set('is_away_from_key', data['away_from_key'])
    if not app.state_manager.getARQ() and data['enabled']:
        await enqueue_tx_command(command_beacon.BeaconCommand, data)
    return api_response({"enabled": data['enabled'], "away_from_key": data['away_from_key']})


@app.post("/modem/ping_ping", summary="Trigger Modem to PING a Station", tags=["Modem"], responses={
    200: {
        "description": "Ping command sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": True
                }
            }
        }
    },
    400: {
        "description": "Invalid input parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid 'dxcall' parameter."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_ping(request: Request):
    """
    Trigger the modem to send a PING to a station.

    Parameters:
        request (Request): The HTTP request containing the following JSON key:
            - 'dxcall' (str): Callsign of the station to ping.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If parameters are invalid or modem is not running.
    """
    data = await request.json()
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    dxcall = data.get('dxcall')
    if not dxcall or not validations.validate_freedata_callsign(dxcall):
        api_abort("Invalid 'dxcall' parameter.", 400)
    await enqueue_tx_command(command_ping.PingCommand, data)
    return api_response({"message": True})


@app.post("/modem/send_test_frame", summary="Send Test Frame", tags=["Modem"], responses={
    200: {
        "description": "Test frame sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "ok"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_send_test_frame():
    """
    Trigger the modem to send a test frame.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running.
    """
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(command_test.TestCommand)
    return api_ok()

@app.post("/modem/fec_transmit", summary="FEC Transmit", tags=["Modem"], responses={
    200: {
        "description": "FEC frame transmitted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "FEC transmission started."
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid parameters."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_send_fec_frame(request: Request):
    """
    Trigger the modem to transmit a Forward Error Correction (FEC) frame.

    Parameters:
        request (Request): The HTTP request containing transmission parameters in JSON format.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running, the request is malformed, or an internal error occurs.
    """
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)

    try:
        data = await request.json()
    except Exception:
        api_abort("Invalid parameters.", 400)

    # Validate required parameters (adjust based on actual requirements)
    if 'message' not in data:
        api_abort("Invalid parameters: 'message' field is required.", 400)

    # Enqueue the FEC transmission command
    try:
        await enqueue_tx_command(command_fec.FecCommand, data)
        return api_response({"message": "FEC transmission started."})
    except Exception as e:
        # Log the exception if necessary
        api_abort("Internal server error.", 500)


from fastapi import HTTPException

@app.get("/modem/fec_is_writing", summary="Indicate User is Typing (FEC)", tags=["Modem"], responses={
    501: {
        "description": "Feature not implemented.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Feature not implemented yet."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_fec_is_writing():
    """
    Trigger the modem to inform over RF that the user is typing a message.

    Returns:
        dict: A JSON object indicating that the feature is not implemented.

    Raises:
        HTTPException: If the modem is not running or the feature is not implemented.
    """
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)

    # Since the feature is not implemented yet, return a 501 Not Implemented error
    raise HTTPException(status_code=501, detail="Feature not implemented yet.")


@app.post("/modem/start", summary="Start Modem", tags=["Modem"], responses={
    200: {
        "description": "Modem started successfully.",
        "content": {
            "application/json": {
                "examples": {
                    "modem_started": {
                        "summary": "Modem Started",
                        "value": {
                            "modem": "started"
                        }
                    },
                    "message_ok": {
                        "summary": "Message OK",
                        "value": {
                            "message": "ok"
                        }
                    }
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid parameters."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    }
})
async def post_modem_start(request: Request):
    """
    Trigger the modem to start.

    Parameters:
        request (Request): The HTTP request containing the following JSON key:
            - 'start' (bool): True to start the modem.

    Returns:
        dict: A JSON object indicating the modem has started.

    Raises:
        HTTPException: If parameters are invalid or an error occurs.
    """
    try:
        data = await request.json()
        if 'start' not in data or not isinstance(data['start'], bool):
            api_abort("Invalid parameters.", 400)
        if not data['start']:
            api_abort("Invalid 'start' parameter. Must be True.", 400)
    except Exception:
        api_abort("Invalid parameters.", 400)

    try:
        app.modem_service.put("start")
        return api_response({"modem": "started"})
    except Exception as e:
        api_abort("Internal server error.", 500)


@app.post("/modem/stop", summary="Stop Modem", tags=["Modem"], responses={
    200: {
        "description": "Modem stopped successfully.",
        "content": {
            "application/json": {
                "examples": {
                    "modem_stopped": {
                        "summary": "Modem Stopped",
                        "value": {
                            "modem": "stopped"
                        }
                    },
                    "message_ok": {
                        "summary": "Message OK",
                        "value": {
                            "message": "ok"
                        }
                    }
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_modem_stop():
    """
    Trigger the modem to stop.

    Returns:
        dict: A JSON object indicating the modem has stopped.

    Raises:
        HTTPException: If the modem is not running or an error occurs.
    """
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)

    try:
        app.modem_service.put("stop")
        return api_response({"modem": "stopped"})
    except Exception:
        api_abort("Internal server error.", 500)


@app.get("/version", summary="Get Modem Version", tags=["General"], responses={
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "api_version": 3,
                    "modem_version": "0.16.8-alpha",
                    "os_info": {
                        "system": "Linux",
                        "node": "my-node",
                        "release": "5.4.0-74-generic",
                        "version": "#83-Ubuntu SMP Mon May 10 16:30:51 UTC 2021",
                        "machine": "x86_64",
                        "processor": "x86_64"
                    },
                    "python_info": {
                        "build": ["default", "May  3 2021 19:12:05"],
                        "compiler": "GCC 9.3.0",
                        "branch": "",
                        "implementation": "CPython",
                        "revision": "",
                        "version": "3.8.5"
                    }
                }
            }
        }
    }
})
async def get_modem_version():
    """
    Retrieve the modem version, API version, OS information, and Python information.

    Returns:
        dict: A JSON object containing version information.
    """
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

@app.post("/modem/send_arq_raw", summary="Send ARQ Raw Data", tags=["Modem"], responses={
    200: {
        "description": "ARQ raw data sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "data": "RnJlZURBVEEgaXMgdGhlIGJlc3Qh",
                    "dxcall": "XX1XXX-6",
                    "type": "raw"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running or busy.",
        "content": {
            "application/json": {
                "examples": {
                    "modem_not_running": {
                        "summary": "Modem Not Running",
                        "value": {
                            "error": "Modem not running."
                        }
                    },
                    "modem_busy": {
                        "summary": "Modem Busy",
                        "value": {
                            "error": "Modem Busy."
                        }
                    }
                }
            }
        }
    }
})
async def post_send_arq_raw(request: Request):
    """
    Send ARQ raw data to a specified station.

    Parameters:
        request (Request): The HTTP request containing the following JSON keys:
            - 'dxcall' (str): Callsign of the station to send data to.
            - 'type' (str): Data type ('raw', 'raw_lzma', 'raw_gzip').
            - 'data' (str): Base64 encoded data to send.

    Returns:
        dict: A JSON object echoing the sent data.

    Raises:
        HTTPException: If parameters are invalid or modem is not running/busy.
    """
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running.", 503)
    if app.state_manager.is_modem_busy:
        api_abort("Modem Busy.", 503)
    data = await request.json()
    dxcall = data.get('dxcall')
    data_type = data.get('type')
    raw_data = data.get('data')
    if not dxcall or not validations.validate_freedata_callsign(dxcall):
        api_abort("Invalid 'dxcall' parameter.", 400)
    if data_type not in ['raw', 'raw_lzma', 'raw_gzip']:
        api_abort("Invalid 'type' parameter.", 400)
    if not raw_data:
        api_abort("Missing 'data' parameter.", 400)
    await enqueue_tx_command(command_arq_raw.SendARQRawCommand, data)
    return api_response({
        "data": raw_data,
        "dxcall": dxcall,
        "type": data_type
    })


@app.post("/modem/stop_transmission", summary="Stop Transmission", tags=["Modem"], responses={
    200: {
        "description": "Transmission stopped successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "ok"
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid request."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_modem_stop_transmission():
    """
    Stop the current transmission.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running or an error occurs.
    """
    if not app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    if app.state_manager.getARQ():
        try:
            for session in app.state_manager.arq_irs_sessions.values():
                # session.abort_transmission()
                session.transmission_aborted()
            for session in app.state_manager.arq_iss_sessions.values():
                session.abort_transmission(send_stop=False)
                session.transmission_aborted()
        except Exception as e:
            print(f"Error during transmission stopping: {e}")
    return api_ok()


@app.get("/radio", summary="Get Radio Parameters", tags=["Radio"], responses={
    200: {
        "description": "Current radio parameters.",
        "content": {
            "application/json": {
                "example": {
                    "radio_frequency": "14093000",
                    "radio_mode": "PKTUSB",
                    "radio_rf_level": 100,
                    "radio_status": True,
                    "radio_swr": 0,
                    "radio_tuner": False,
                    "s_meter_strength": "20"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def get_radio():
    """
    Retrieve current radio parameters.

    Returns:
        dict: A JSON object containing radio parameters.
    """
    return app.state_manager.get_radio_status()


@app.post("/radio", summary="Set Radio Parameters", tags=["Radio"], responses={
    200: {
        "description": "Radio parameters updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "radio_frequency": "14093000",
                    "radio_mode": "PKTUSB",
                    "radio_rf_level": 100,
                    "radio_status": True,
                    "radio_swr": 0,
                    "radio_tuner": True,
                    "s_meter_strength": "20"
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid parameters."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def post_radio(request: Request):
    """
    Set radio parameters.

    Parameters:
        request (Request): The HTTP request containing the radio parameters in JSON format.

    Returns:
        dict: A JSON object containing the updated radio parameters.
    """
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


@app.post("/radio/tune", summary="Enable/Disable Radio Tuning", tags=["Radio"], responses={
    200: {
        "description": "Radio tuning status updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "enable_tuning": True
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid parameters."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running or busy.",
        "content": {
            "application/json": {
                "examples": {
                    "modem_not_running": {
                        "summary": "Modem Not Running",
                        "value": {
                            "error": "Modem not running."
                        }
                    },
                    "modem_busy": {
                        "summary": "Modem Busy",
                        "value": {
                            "error": "Modem Busy."
                        }
                    }
                }
            }
        }
    }
})
async def post_radio_tune(request: Request):
    """
    Trigger the modem to inform over RF that the user is typing a message.

    Parameters:
        request (Request): The HTTP request containing the following JSON key:
            - 'enable_tuning' (bool): True to enable tuning, False to disable.

    Returns:
        dict: A JSON object echoing the tuning status.

    Raises:
        HTTPException: If the modem is not running/busy or if parameters are invalid.
    """
    data = await request.json()
    print(data)
    if "enable_tuning" in data:
        if data['enable_tuning']:
            if not app.state_manager.is_modem_running:
                api_abort("Modem not running", 503)
            await enqueue_tx_command(command_transmit_sine.TransmitSine)
        else:
            app.service_manager.modem.stop_sine()
    else:
        app.service_manager.modem.stop_sine()

    return api_response(data)



@app.get("/freedata/messages/{message_id}", summary="Get Message by ID", tags=["FreeDATA"], responses={
    200: {"description": "Message found and returned."},
    404: {"description": "Message not found."}
})
async def get_freedata_message(message_id: str):
    message = DatabaseManagerMessages(app.event_manager).get_message_by_id_json(message_id)
    return api_response(message)


@app.post("/freedata/messages", summary="Transmit Message", tags=["FreeDATA"], responses={
    200: {
        "description": "Message transmitted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "destination": "XX1XXX-6",
                    "body": "Hello FreeDATA"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running or busy.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_freedata_message(request: Request):
    """
    Transmit a FreeDATA message.

    Parameters:
        request (Request): The HTTP request containing the message data in JSON format.

    Returns:
        dict: A JSON object containing the transmitted message details.
    """
    data = await request.json()
    await enqueue_tx_command(command_message_send.SendMessageCommand, data)
    return api_response(data)

@app.post("/freedata/messages/{message_id}/adif", summary="Send Message ADIF Log", tags=["FreeDATA"], responses={
    200: {
        "description": "ADIF log sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "adif_output": "ADIF data..."
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid message ID."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Message not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_freedata_message_adif_log(message_id: str):
    adif_output = DatabaseManagerMessages(app.event_manager).get_message_by_id_adif(message_id)
    # Send the ADIF data via UDP
    adif_udp_logger.send_adif_qso_data(app.config_manager.read(), adif_output)
    return api_response(adif_output)

@app.patch("/freedata/messages/{message_id}", summary="Update Message by ID", tags=["FreeDATA"], responses={
    200: {
        "description": "Message updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "is_read": True
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid parameters."
                }
            }
        }
    },
    404: {
        "description": "Message not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Message not found."
                }
            }
        }
    }
})
async def patch_freedata_message(message_id: str, request: Request):
    """
    Update a FreeDATA message by its ID.

    Parameters:
        message_id (str): The ID of the message to update.
        request (Request): The HTTP request containing the update data in JSON format.

    Returns:
        dict: A JSON object containing the updated message details.
    """
    data = await request.json()

    if data.get("action") == "retransmit":
        result = DatabaseManagerMessages(app.event_manager).update_message(message_id, update_data={'status': 'queued'})
        DatabaseManagerMessages(app.event_manager).increment_message_attempts(message_id)
    else:
        result = DatabaseManagerMessages(app.event_manager).update_message(message_id, update_data=data)

    return api_response(result)


@app.get("/freedata/messages", summary="Get All Messages", tags=["FreeDATA"], responses={
    200: {
        "description": "List of all messages.",
        "content": {
            "application/json": {
                "example": {
                    "total_messages": 1,
                    "messages": [
                        {
                            "id": "DXCALL-6_MYCALL-0_2024-04-12T20:39:05.302479",
                            "timestamp": "2024-04-12T20:39:05.302479",
                            "origin": "DXCALL-6",
                            "via": None,
                            "destination": "MYCALL-0",
                            "direction": "receive",
                            "body": "Hello !",
                            "attachments": [],
                            "status": "received",
                            "priority": 10,
                            "is_read": False,
                            "statistics": {
                                "total_bytes": 120,
                                "duration": 29.76698660850525,
                                "bytes_per_minute": 241,
                                "time_histogram": {
                                    "0": "2024-04-12T20:39:23.423169",
                                    "1": "2024-04-12T20:39:30.504638",
                                    "2": "2024-04-12T20:39:37.745075"
                                },
                                "snr_histogram": {
                                    "0": -6,
                                    "1": -6,
                                    "2": -6
                                },
                                "bpm_histogram": {
                                    "0": 198,
                                    "1": 265,
                                    "2": 252
                                }
                            }
                        }
                    ]
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def get_freedata_messages(request: Request):
    filters = {k: v for k, v in request.query_params.items() if v}
    result = DatabaseManagerMessages(app.event_manager).get_all_messages_json(filters=filters)
    return api_response(result)


@app.post("/freedata/messages", summary="Transmit Message", tags=["FreeDATA"], responses={
    200: {
        "description": "Message transmitted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "destination": "XX1XXX-6",
                    "body": "Hello FreeDATA"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def post_freedata_message(request: Request):
    """
    Transmit a FreeDATA message.

    Parameters:
        request (Request): The HTTP request containing the message data in JSON format.

    Returns:
        dict: A JSON object containing the transmitted message details.
    """
    data = await request.json()
    await enqueue_tx_command(command_message_send.SendMessageCommand, data)
    return api_response(data)



@app.delete("/freedata/messages/{message_id}", summary="Delete Message by ID", tags=["FreeDATA"], responses={
    200: {
        "description": "Message deleted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502 deleted",
                    "status": "success"
                }
            }
        }
    },
    404: {
        "description": "Message not found.",
        "content": {
            "application/json": {
                "example": {
                    "message": "Message not found",
                    "status": "failure"
                }
            }
        }
    }
})
async def delete_freedata_message(message_id: str):
    result = DatabaseManagerMessages(app.event_manager).delete_message(message_id)
    if result:
        return api_response({"message": f"{message_id} deleted", "status": "success"})
    else:
        return api_response({"message": "Message not found", "status": "failure"}, status_code=404)


@app.get("/freedata/messages/{message_id}/attachments", summary="Get Attachments by Message ID", tags=["FreeDATA"], responses={
    200: {
        "description": "List of attachments for the specified message.",
        "content": {
            "application/json": {
                "example": {
                    "attachments": [
                        {
                            "id": "attachment1",
                            "filename": "file1.txt",
                            "file_size": 1024,
                            "file_type": "text/plain",
                            "data_sha512": "abcdef1234567890..."
                        },
                        {
                            "id": "attachment2",
                            "filename": "image.png",
                            "file_size": 2048,
                            "file_type": "image/png",
                            "data_sha512": "123456abcdef7890..."
                        }
                    ]
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_message_attachments(message_id: str):
    attachments = DatabaseManagerAttachments(app.event_manager).get_attachments_by_message_id_json(message_id)
    return api_response(attachments)


@app.get("/freedata/messages/attachment/{data_sha512}", summary="Get Attachment by SHA512", tags=["FreeDATA"], responses={
    200: {
        "description": "Retrieve a specific attachment by its SHA512 hash.",
        "content": {
            "application/json": {
                "example": {
                    "id": "attachment1",
                    "filename": "file1.txt",
                    "file_size": 1024,
                    "file_type": "text/plain",
                    "data_sha512": "abcdef1234567890..."
                }
            }
        }
    },
    404: {
        "description": "The requested attachment was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Attachment not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_message_attachment(data_sha512: str):
    attachment = DatabaseManagerAttachments(app.event_manager).get_attachment_by_sha512(data_sha512)
    return api_response(attachment)


@app.get("/freedata/beacons", summary="Get Received Beacons", tags=["FreeDATA"], responses={
    200: {
        "description": "List of received beacons.",
        "content": {
            "application/json": {
                "example": {
                    "total_beacons": 2,
                    "beacons": [
                        {
                            "id": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502",
                            "timestamp": "2024-04-04T17:22:14.002502",
                            "origin": "DXCALL-0",
                            "via": None,
                            "destination": "MYCALL-5",
                            "direction": "receive",
                            "body": "Hello FreeDATA",
                            "attachments": [],
                            "status": "received",
                            "priority": 10,
                            "is_read": False,
                            "statistics": {
                                "total_bytes": 120,
                                "duration": 29.77,
                                "bytes_per_minute": 241,
                                "time_histogram": {
                                    "0": "2024-04-04T17:22:23.423169",
                                    "1": "2024-04-04T17:22:30.504638",
                                    "2": "2024-04-04T17:22:37.745075"
                                },
                                "snr_histogram": {
                                    "0": -6,
                                    "1": -6,
                                    "2": -6
                                },
                                "bpm_histogram": {
                                    "0": 198,
                                    "1": 265,
                                    "2": 252
                                }
                            }
                        }
                    ]
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid request."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_all_beacons():
    beacons = DatabaseManagerBeacon(app.event_manager).get_all_beacons()
    return api_response(beacons)


@app.get("/freedata/beacons/{callsign}", summary="Get Beacon by Callsign", tags=["FreeDATA"], responses={
    200: {
        "description": "List of beacons from the specified callsign.",
        "content": {
            "application/json": {
                "example": {
                    "beacons": [
                        {
                            "id": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502",
                            "timestamp": "2024-04-04T17:22:14.002502",
                            "origin": "DXCALL-0",
                            "via": None,
                            "destination": "MYCALL-5",
                            "direction": "receive",
                            "body": "Hello FreeDATA",
                            "attachments": [],
                            "status": "received",
                            "priority": 10,
                            "is_read": False,
                            "statistics": {
                                "total_bytes": 120,
                                "duration": 29.77,
                                "bytes_per_minute": 241,
                                "time_histogram": {
                                    "0": "2024-04-04T17:22:23.423169",
                                    "1": "2024-04-04T17:22:30.504638",
                                    "2": "2024-04-04T17:22:37.745075"
                                },
                                "snr_histogram": {
                                    "0": -6,
                                    "1": -6,
                                    "2": -6
                                },
                                "bpm_histogram": {
                                    "0": 198,
                                    "1": 265,
                                    "2": 252
                                }
                            }
                        }
                    ]
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid request."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_beacons_by_callsign(callsign: str):
    beacons = DatabaseManagerBeacon(app.event_manager).get_beacons_by_callsign(callsign)
    return api_response(beacons)


@app.get("/freedata/station/{callsign}", summary="Get Station Info", tags=["FreeDATA"], responses={
    200: {
        "description": "Retrieve station information by callsign.",
        "content": {
            "application/json": {
                "example": {
                    "callsign": "MYCALL-0",
                    "location": "Springfield",
                    "frequency": "14093000",
                    "mode": "PKTUSB",
                    "status": "active",
                    "additional_info": "Station details here."
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid callsign parameter."
                }
            }
        }
    },
    404: {
        "description": "The requested station was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Station not found."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_station_info(callsign: str):
    station = DatabaseManagerStations(app.event_manager).get_station(callsign)
    return api_response(station)


@app.post("/freedata/station/{callsign}", summary="Set Station Info", tags=["FreeDATA"], responses={
    200: {
        "description": "Station information updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "callsign": "MYCALL-0",
                    "location": "Springfield",
                    "frequency": "14093000",
                    "mode": "PKTUSB",
                    "status": "active",
                    "additional_info": "Updated station details."
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid input data."
                }
            }
        }
    },
    404: {
        "description": "The requested station was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Station not found."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
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
