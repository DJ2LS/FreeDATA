# -*- coding: UTF-8 -*-
"""
Created on 05.11.23

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import requests
import threading
import json
import structlog
import sched
import time

log = structlog.get_logger("explorer")

class explorer():
    def __init__(self, modem_version, config_manager, states):
        self.modem_version = modem_version

        self.config_manager = config_manager
        self.config = self.config_manager.read()
        self.states = states
        self.explorer_url = "https://api.freedata.app/explorer.php"

    def push(self):
        self.config = self.config_manager.read()

        frequency = 0 if self.states.radio_frequency is None else self.states.radio_frequency
        band = "USB"
        callsign = str(self.config['STATION']['mycall']) + "-" + str(self.config["STATION"]['myssid'])
        gridsquare = str(self.config['STATION']['mygrid'])
        version = str(self.modem_version)
        bandwidth = str(self.config['MODEM']['maximum_bandwidth'])
        beacon = str(self.states.is_beacon_running)
        strength = str(self.states.s_meter_strength)
        away_from_key = str(self.states.is_away_from_key)

        # stop pushing if default callsign
        if callsign in ['XX1XXX-6']:
            return

        # disabled this one
        # log.info("[EXPLORER] publish", frequency=frequency, band=band, callsign=callsign, gridsquare=gridsquare, version=version, bandwidth=bandwidth)

        headers = {"Content-Type": "application/json"}
        station_data = {'callsign': callsign, 'gridsquare': gridsquare, 'frequency': frequency, 'strength': strength, 'band': band, 'version': version, 'bandwidth': bandwidth, 'beacon': beacon, "lastheard": [], "away_from_key": away_from_key}

        for i in self.states.heard_stations:
            try:
                callsign = i[0]
                grid = i[1]
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

        except Exception as e:
            log.warning("[EXPLORER] connection lost")
