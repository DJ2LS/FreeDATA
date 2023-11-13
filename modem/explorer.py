# -*- coding: UTF-8 -*-
"""
Created on 05.11.23

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import requests
import threading
import ujson as json
import structlog
from global_instances import HamlibParam, Modem

log = structlog.get_logger("explorer")

class explorer():
    def __init__(self, config, states):
        self.config = config
        self.states = states
        self.explorer_url = "https://api.freedata.app/explorer.php"
        self.publish_interval = 120
        self.enable_explorer = config["STATION"]["enable_explorer"]

        if self.enable_explorer:
            self.interval_thread = threading.Thread(target=self.interval, name="interval", daemon=True)
            self.interval_thread.start()

    def interval(self):
        while True:
            self.push()
            threading.Event().wait(self.publish_interval)

    def push(self):

        frequency = 0 if HamlibParam.hamlib_frequency is None else HamlibParam.hamlib_frequency
        band = "USB"
        callsign = str(self.config['STATION']['mycall'])
        gridsquare = str(self.config['STATION']['mygrid'])
        version = str(Modem.version)
        bandwidth = str(self.config['MODEM']['enable_low_bandwidth_mode'])
        beacon = str(self.states.is_beacon_running)
        strength = str(HamlibParam.hamlib_strength)

        log.info("[EXPLORER] publish", frequency=frequency, band=band, callsign=callsign, gridsquare=gridsquare, version=version, bandwidth=bandwidth)

        headers = {"Content-Type": "application/json"}
        station_data = {'callsign': callsign, 'gridsquare': gridsquare, 'frequency': frequency, 'strength': strength, 'band': band, 'version': version, 'bandwidth': bandwidth, 'beacon': beacon, "lastheard": []}

        for i in Modem.heard_stations:
            try:
                callsign = str(i[0], "UTF-8")
                grid = str(i[1], "UTF-8")
                timestamp = i[2]
                frequency = i[6]
                try:
                    snr = i[4].split("/")[1]
                except AttributeError:
                    snr = str(i[4])
                station_data["lastheard"].append({"callsign": callsign, "grid": grid, "snr": snr, "timestamp": timestamp, "frequency": frequency})
            except Exception as e:
                log.debug("[EXPLORER] not publishing station", e=e)

        station_data = json.dumps(station_data)
        try:
            response = requests.post(self.explorer_url, json=station_data, headers=headers)
            # print(response.status_code)
            # print(response.content)

        except Exception as e:
            log.warning("[EXPLORER] connection lost")
