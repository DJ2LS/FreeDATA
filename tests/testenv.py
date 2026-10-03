"""Shared test environment.

Keeps tests away from the repository's config template and the user's real
FreeDATA app directory: every test run gets its own temporary config file and
message database. Import this module before creating an AppContext.
"""

import atexit
import os
import shutil
import tempfile

_REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_TEMPLATE = os.path.join(_REPO_DIR, "freedata_server", "config.ini.example")

_TMP_DIR = tempfile.mkdtemp(prefix="freedata-tests-")
atexit.register(shutil.rmtree, _TMP_DIR, ignore_errors=True)

os.environ.setdefault("FREEDATA_DATABASE", os.path.join(_TMP_DIR, "freedata-messages.db"))


def config_path():
    """Return the path of a temporary copy of config.ini.example."""
    path = os.path.join(_TMP_DIR, "config.ini")
    if not os.path.exists(path):
        shutil.copyfile(CONFIG_TEMPLATE, path)
    return path
