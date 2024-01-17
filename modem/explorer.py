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
import sched
import time

log = structlog.get_logger("explorer")

class explorer():
    def __init__(self, app, config, states):
        self.config = config
        self.app = app
        self.states = states
        self.explorer_url = "https://api.freedata.app/explorer.php"
        self.publish_interval = 120

        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.schedule_thread = threading.Thread(target=self.run_scheduler)
        self.schedule_thread.start()

    def run_scheduler(self):
        # Schedule the first execution of push
        self.scheduler.enter(self.publish_interval, 1, self.push)
        # Run the scheduler in a loop
        self.scheduler.run()

    def push(self):

        frequency = 0 if self.states.radio_frequency is None else self.states.radio_frequency
        band = "USB"
        callsign = str(self.config['STATION']['mycall']) + "-" + str(self.config["STATION"]['myssid'])
        gridsquare = str(self.config['STATION']['mygrid'])
        version = str(self.app.MODEM_VERSION)
        bandwidth = str(self.config['MODEM']['enable_low_bandwidth_mode'])
        beacon = str(self.states.is_beacon_running)
        strength = str(self.states.s_meter_strength)

        log.info("[EXPLORER] publish", frequency=frequency, band=band, callsign=callsign, gridsquare=gridsquare, version=version, bandwidth=bandwidth)

        headers = {"Content-Type": "application/json"}
        station_data = {'callsign': callsign, 'gridsquare': gridsquare, 'frequency': frequency, 'strength': strength, 'band': band, 'version': version, 'bandwidth': bandwidth, 'beacon': beacon, "lastheard": []}

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

        # Reschedule the push method
        self.scheduler.enter(self.publish_interval, 1, self.push)

        def shutdown(self):
            # If there are other cleanup tasks, include them here
            if self.schedule_thread:
                self.schedule_thread.join()
