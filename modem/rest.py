#!/usr/bin/env python
# encoding: utf-8
import config
import threading
from flask import Flask, jsonify
import structlog
import rest_handler
import sys
log = structlog.get_logger("REST")

app_name = "FreeDATA REST API"
app = Flask(app_name)
conf = config.CONFIG('config.ini')
encoding = 'utf-8'

@app.route('/', methods=['GET'])
def index():
    return jsonify({'name': app_name,
                    'description': '',
                    'api_version': 1,
                    'license': 'GPL3.0',
                    'documentation': 'https://wiki.freedata.app',
                    })

@app.route('/config', methods=['GET'])
def config():
    return jsonify(rest_handler.get_running_config())


class REST:
    def __init__(self):
        self.flask_thread = threading.Thread(app.run(host='localhost', port='5000', debug=False, use_reloader=False))

    def start(self):
        try:
            self.flask_thread.start()
        except Exception as e:
            log.error("[REST] error while starting rest api", e=e)
            sys.exit(1)

    def stop(self):
        try:
            self.flask_thread.stop()
        except Exception as e:
            log.error("[REST] error while stopping rest api", e=e)
