# -*- coding: UTF-8 -*-
"""
Created on 05.11.23

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import requests
import threading
import time
import ujson as json
import structlog
import static

log = structlog.get_logger("explorer")


class explorer():
    def __init__(self):
        self.explorer_url = "https://explorer.freedata.app/api.php"
        self.publish_interval = 120

        self.interval_thread = threading.Thread(target=self.interval, name="interval", daemon=True)
        self.interval_thread.start()

    def interval(self):
        while True:
            self.push()
            time.sleep(self.publish_interval)

    def push(self):


        if static.HAMLIB_FREQUENCY is not None:
            frequency = static.HAMLIB_FREQUENCY
        else:
            frequency = 0
        band = "USB"
        callsign = str(static.MYCALLSIGN, "utf-8")
        gridsquare = str(static.MYGRID, "utf-8")
        version = str(static.VERSION)
        bandwidth = str(static.LOW_BANDWIDTH_MODE)
        beacon = str(static.BEACON_STATE)

        log.info("[EXPLORER] publish", frequency=frequency, band=band, callsign=callsign, gridsquare=gridsquare, version=version, bandwidth=bandwidth)

        headers = {"Content-Type": "application/json"}
        station_data = {'callsign': callsign, 'gridsquare': gridsquare, 'frequency': frequency, 'band': band, 'version': version, 'bandwidth': bandwidth, 'beacon': beacon}
        station_data = json.dumps(station_data)
        try:
            response = requests.post(self.explorer_url, json=station_data, headers=headers)
            # print(response.status_code)
            # print(response.content)

        except Exception as e:
            log.warning("[EXPLORER] connection lost")
