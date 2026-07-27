# Module for saving some constants
import os
import sys


def _default_app_dir() -> str:
    """
    Per-user directory for config, database and log file, following each
    OS's own convention rather than forcing a single layout everywhere:
      - Windows: %APPDATA%\\FreeDATA
      - macOS:   ~/Library/Application Support/FreeDATA
      - Linux:   $XDG_CONFIG_HOME/FreeDATA or ~/.config/FreeDATA
    Used only when FREEDATA_CONFIG / FREEDATA_DATABASE are not set (e.g. a
    plain `pip install freedata` run). Keeping this outside the installed
    package directory means it survives package upgrades/reinstalls.
    """
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        base = os.getenv("APPDATA") or home
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.getenv("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    return os.path.join(base, "FreeDATA")


CONFIG_ENV_VAR = "FREEDATA_CONFIG"
DEFAULT_CONFIG_FILE = "config.ini"
DEFAULT_APP_DIR = _default_app_dir()
MODEM_VERSION = "0.18.2"
API_VERSION = 4
ARQ_PROTOCOL_VERSION = 1
LICENSE = "GPL3.0"
DOCUMENTATION_URL = "https://wiki.freedata.app"
STATS_API_URL = "https://api.freedata.app/stats.php"
EXPLORER_API_URL = "https://api.freedata.app/explorer.php"
MESSAGE_SYSTEM_DATABASE_VERSION = 1
