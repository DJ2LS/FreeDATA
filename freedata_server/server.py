
import os
import sys
# we need to add script directory to the sys path for avoiding problems with pip package
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)

import signal
import queue
import asyncio
import webbrowser
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import threading
from config import CONFIG
import audio
import service_manager
import state_manager
import websocket_manager
import event_manager
import structlog


from message_system_db_manager import DatabaseManager
from message_system_db_attachments import DatabaseManagerAttachments
from schedule_manager import ScheduleManager

from api.general import router as general_router
from api.config import router as config_router
from api.devices import router as devices_router
from api.radio import router as radio_router
from api.modem import router as modem_router
from api.freedata import router as freedata_router
from api.websocket import router as websocket_router
from constants import CONFIG_ENV_VAR, DEFAULT_CONFIG_FILE, MODEM_VERSION, API_VERSION, LICENSE, DOCUMENTATION_URL

# adjust asyncio for windows usage for avoiding a Assertion Error
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    #print("startup")
    yield
    stop_server()

app = FastAPI(lifespan=lifespan)
app.include_router(general_router, prefix="")
app.include_router(config_router, prefix="/config")
app.include_router(devices_router, prefix="/devices")
app.include_router(radio_router, prefix="/radio")
app.include_router(modem_router, prefix="/modem")
app.include_router(freedata_router, prefix="/freedata")
app.include_router(websocket_router, prefix="")
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
async def http_middleware(request: Request, call_next):
    """Middleware function for HTTP requests.

    This middleware function intercepts HTTP requests, disables caching,
    logs request details (method, URL, and response code), and passes the
    request to the next middleware or route handler. It also includes
    commented-out code for enabling caching, which can be activated if
    needed.

    Args:
        request (Request): The incoming HTTP request.
        call_next: The next middleware function or route handler in the chain.

    Returns:
        Response: The HTTP response.
    """
    response = await call_next(request)

    # Disable caching
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"  # For HTTP/1.0 backward compatibility

    # Enable caching for 1 day
    # response.headers["Cache-Control"] = "public, max-age=86400"  # Cache for 86400 seconds (1 day)
    # response.headers["Pragma"] = "cache"  # backward compatibility with HTTP/1.0
    # response.headers["Expires"] = "0"  # Forces modern clients to use max-age

    # Log requests
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




# Set config file to use
def set_config():
    """Sets the configuration file to use.

    This function retrieves the path to the configuration file from the
    environment variable CONFIG_ENV_VAR or defaults to DEFAULT_CONFIG_FILE
    in the script directory. It checks if the file exists and exits the
    program if not found.

    Returns:
        str: The path to the configuration file.
    """
    config_file = os.getenv(CONFIG_ENV_VAR, os.path.join(script_directory, DEFAULT_CONFIG_FILE))
    if os.path.exists(config_file):
        print(f"Using config from {config_file}")
    else:
        print(f"Config file '{config_file}' not found. Exiting.")
        sys.exit(1)
    return config_file






# Signal Handler
def signal_handler(sig, frame):
    """Handles SIGINT signal (Ctrl+C).

    This function is called when the user interrupts the server with
    Ctrl+C (SIGINT signal). It logs a warning message and initiates the
    server shutdown process. The frame argument is not currently used.

    Args:
        sig: The signal number (SIGINT).
        frame: The current stack frame.
    """
    print("\n------------------------------------------")
    logger.warning("[SHUTDOWN] Received SIGINT....")
    stop_server()

def stop_server():
    """Stops the FreeDATA server and its components.

    This function performs a graceful shutdown of the FreeDATA server,
    including stopping transmissions, shutting down various managers and
    services, closing socket interfaces, and terminating audio streams.
    It attempts to handle potential errors during the shutdown process.
    """
    # INFO attempt stopping ongoing transmission for reducing chance of stuck PTT
    if hasattr(app, 'state_manager'):
        logger.warning("[SHUTDOWN] Stopping ongoing transmissions....")
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
    """Opens the specified URL in a web browser after a delay.

    This function opens the given URL in a new browser window or tab after
    a specified delay. It is used to automatically open the FreeDATA GUI
    in a browser after the server has started.

    Args:
        url (str): The URL to open.
        delay (int, optional): The delay in seconds before opening the browser. Defaults to 2.
    """
    threading.Event().wait(delay)
    webbrowser.open(url, new=0, autoraise=True)

def main():
    """Main function to start the FreeDATA server.

    This function initializes the FreeDATA server, sets up signal
    handling, configures managers and services, starts the modem,
    initializes the database, starts websocket workers, and runs the
    FastAPI server using uvicorn. It also handles automatic opening of
    the GUI in a web browser.
    """
    signal.signal(signal.SIGINT, signal_handler)

    app.MODEM_VERSION = MODEM_VERSION
    app.API_VERSION = API_VERSION

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
    DatabaseManager(app.event_manager).check_database_version()
    DatabaseManager(app.event_manager).initialize_default_values()
    DatabaseManager(app.event_manager).database_repair_and_cleanup()
    DatabaseManagerAttachments(app.event_manager).clean_orphaned_attachments()

    app.wsm = websocket_manager.wsm()
    app.wsm.startWorkerThreads(app)

    conf = app.config_manager.read()
    modemaddress = conf['NETWORK'].get('modemaddress', '127.0.0.1')
    modemport = int(conf['NETWORK'].get('modemport', 5000))

    # check if modemadress is empty - known bug caused by older versions
    if modemaddress in ['', None]:
        modemaddress = '127.0.0.1'

    if modemport in ['', None]:
        modemport = 5000  # Use integer value

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
