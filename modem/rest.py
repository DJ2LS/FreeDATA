#!/usr/bin/env python
# encoding: utf-8
import config
import threading
import ujson as json
from flask import Flask, jsonify
import structlog
import sys
log = structlog.get_logger("REST")


from global_instances import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem, MeshParam

app_name = "FreeDATA REST API"
app = Flask(app_name)
conf = config.CONFIG('config.ini')
encoding = 'utf-8'


@app.route('/', methods=['GET'])
def index():
    return jsonify({'name': app_name,
                    'description': '',
                    'api_version': 1,
                    'modem_version': Modem.version,
                    'license': 'GPL3.0',
                    'documentation': 'https://wiki.freedata.app',
                    })

@app.route('/config', methods=['GET'])
def config():
    # get config
    dict_config = conf.get_as_dict()
    return jsonify(dict_config)

@app.route('/config/<config_module>', methods=['GET'])
def config_per_module(config_module):
    # get config
    dict_config = conf.get_as_dict(modules=[config_module])
    return jsonify(dict_config)

@app.route('/config/running', methods=['GET'])
def runningconfig():
    # get running config
    try:
        dict_running_config = {
            "AUDIO":
                {
                    "auto_tune":AudioParam.audio_auto_tune,
                    "rx":AudioParam.audio_input_device,
                    "rxaudiolevel":AudioParam.rx_audio_level,
                    "tx":AudioParam.audio_output_device,
                    "txaudiolevel":AudioParam.tx_audio_level
                },
            "MESH":
                {
                    "enable_protocol":MeshParam.enable_protocol
                },
            "Modem":
                {
                    "explorer":Modem.enable_explorer,
                    "fft":AudioParam.enable_fft,
                    "fmax":ModemParam.tuning_range_fmax,
                    "fmin":ModemParam.tuning_range_fmin,
                    "fsk":Modem.enable_fsk,
                    "narrowband":Modem.low_bandwidth_mode,
                    "qrv":Modem.respond_to_cq,
                    "rx_buffer_size":ARQ.rx_buffer_size,
                    "scatter":ModemParam.enable_scatter,
                    "stats": Modem.enable_stats,
                    "transmit_morse_identifier":Modem.transmit_morse_identifier,
                    "tx_delay":ModemParam.tx_delay
                },
            "NETWORK":
                {
                    "modemport":Modem.port
                },
            "RADIO":{
                "radiocontrol":HamlibParam.hamlib_radiocontrol,
                "rigctld_ip":HamlibParam.hamlib_rigctld_ip,
                "rigctld_port":HamlibParam.hamlib_rigctld_port
            },
            "STATION":
                {
                    "mycall": str(Station.mycallsign, encoding),
                    "mygrid": str(Station.mygrid, encoding),
                    "ssid_list": json.dumps(Station.ssid_list),
                },
            "TCI":
                {
                    "ip": TCIParam.ip,
                    "port": TCIParam.port
                }
        }

        return jsonify(dict_running_config)
    except Exception as e:
        log.warning("[REST] error while processing running config", e=e)


class REST:
    def __init__(self):
        self.flask_thread = threading.Thread(target=lambda: app.run(host='localhost', port='5000', debug=False, use_reloader=False))

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
