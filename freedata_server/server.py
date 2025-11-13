import os
import sys

# we need to add script directory to the sys path for avoiding problems with pip package
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)

import threading
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from log_handler import setup_logging
from constants import CONFIG_ENV_VAR, DEFAULT_CONFIG_FILE, API_VERSION
from context import AppContext

import uvicorn


# --- Resolve config path FIRST (no logger needed yet) ---
def resolve_config_path() -> str:
    """
    Determine the configuration file to use (env var or default next to this file).
    Exits if not found.
    """
    candidate = os.getenv(
        CONFIG_ENV_VAR,
        os.path.join(os.path.dirname(__file__), DEFAULT_CONFIG_FILE),
    )
    if not os.path.exists(candidate):
        # We cannot log to file yet since we don't know the directory; write to stderr.
        sys.stderr.write(f"[FATAL] Config file not found: {candidate}\n")
        sys.exit(1)
    return os.path.abspath(candidate)


config_file = resolve_config_path()

# --- Logging setup: log file MUST be in the same directory as the config file ---
config_dir = os.path.dirname(config_file)
log_file = os.path.join(config_dir, "freedata_server.log")
logger = setup_logging(filename=log_file, level="INFO")
logger.info("Using config", file=config_file, log_file=log_file)

# --- AppContext startup ---
ctx = AppContext(config_file)
ctx.startup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # nothing to do on startup here, ctx already initialized
    yield
    # shutdown on exit
    ctx.shutdown()
    logger.info("Shutdown complete")


# Create FastAPI app with unified lifespan
app = FastAPI(
    title="FreeDATA API",
    version=str(API_VERSION),
    lifespan=lifespan,
)

# store ctx for dependency injection
app.state.ctx = ctx

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTP middleware: disable caching and logging
@app.middleware("http")
async def nocache(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    # structlog stdlib logger akzeptiert %-Formatierung; alternativ key/value:
    logger.info("[API] %s %s → %d", request.method, request.url.path, response.status_code)
    return response


# Static GUI mounting
potential_gui_dirs = [
    "../freedata_gui/dist",
    "freedata_gui/dist",
    "FreeDATA/freedata_gui/dist",
    os.path.join(os.path.dirname(__file__), "gui"),
]
gui_dir = next((d for d in potential_gui_dirs if os.path.isdir(d)), None)
if gui_dir:
    app.mount("/gui", StaticFiles(directory=gui_dir, html=True), name="static")
else:
    logger.warning("GUI directory not found: %s", gui_dir)

# Register routers
from api.general import router as general_router
from api.config import router as config_router
from api.devices import router as devices_router
from api.radio import router as radio_router
from api.modem import router as modem_router
from api.freedata import router as freedata_router
from api.websocket import router as websocket_router

app.include_router(general_router, prefix="", tags=["General"])
app.include_router(config_router, prefix="/config", tags=["Configuration"])
app.include_router(devices_router, prefix="/devices", tags=["Devices"])
app.include_router(radio_router, prefix="/radio", tags=["Radio"])
app.include_router(modem_router, prefix="/modem", tags=["Modem"])
app.include_router(freedata_router, prefix="/freedata", tags=["FreeDATA"])
app.include_router(websocket_router, prefix="", tags=["WebSocket"])


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
    host = ctx.config_manager.config.get("NETWORK", {}).get("modemaddress") or "0.0.0.0"
    port = int(ctx.config_manager.config.get("NETWORK", {}).get("modemport", 5000))

    # Launch GUI if available
    if gui_dir and os.path.isdir(gui_dir):
        url = f"http://{host}:{port}/gui"
        logger.info("---------------------------------------------------")
        logger.info("                                                   ")
        logger.info(f"[GUI] AVAILABLE ON {url}")
        logger.info("just open it in your browser")
        logger.info("                                                   ")
        logger.info("---------------------------------------------------")

        if ctx.config_manager.config.get("GUI", {}).get("auto_run_browser", True):
            threading.Thread(target=open_browser_after_delay, args=(url, 2), daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_config=None, log_level="info")


if __name__ == "__main__":
    sys.exit(main())
