#!/usr/bin/env python
# encoding: utf-8
from flask import Flask, jsonify
import structlog
import rest_handler
log = structlog.get_logger("REST")

app_name = "FreeDATA REST API"
app = Flask(app_name)
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
