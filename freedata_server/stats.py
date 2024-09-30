# -*- coding: UTF-8 -*-
"""
Created on 05.11.23

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init
import requests
import json
import structlog

log = structlog.get_logger("stats")

#  we have to move the modem version, its a duplicate
MODEM_VERSION = "0.16.7-alpha"


class stats():
    def __init__(self, config, event_manager, states):
        self.api_url = "https://api.freedata.app/stats.php"
        self.states = states
        self.config = config
        self.event_manager = event_manager
    def push(self, status, session_statistics, dxcall, receiving=True):
        # get avg snr
        try:
            snr_raw = [item["snr"] for item in self.states.arq_speed_list]
            avg_snr = round(sum(snr_raw) / len(snr_raw), 2)
        except Exception:
            avg_snr = 0

        if receiving:
            station = "IRS"
        else:
            station = "ISS"

        mycallsign = self.config['STATION']['mycall']
        ssid = self.config['STATION']['myssid']
        full_callsign = f"{mycallsign}-{ssid}"

        headers = {"Content-Type": "application/json"}
        station_data = {
            'callsign': full_callsign,
            'dxcallsign': dxcall,
            'gridsquare': self.config['STATION']['mygrid'],
            'dxgridsquare': str(self.states.dxgrid, "utf-8"),
            'frequency': 0 if self.states.radio_frequency is None else self.states.radio_frequency,
            'avgsnr': avg_snr,
            'bytesperminute': session_statistics['bytes_per_minute'],
            'filesize': session_statistics['total_bytes'],
            'duration': session_statistics['duration'],
            'status': status,
            'direction': station,
            'version': MODEM_VERSION,
            'time_histogram': session_statistics['time_histogram'],  # Adding new histogram data
            'snr_histogram': session_statistics['snr_histogram'],  # Adding new histogram data
            'bpm_histogram': session_statistics['bpm_histogram'],  # Adding new histogram data
        }

        station_data = json.dumps(station_data)
        print(station_data)
        try:
            response = requests.post(self.api_url, json=station_data, headers=headers)
            log.info("[STATS] push", code=response.status_code)

            # print(response.status_code)
            # print(response.content)

        except Exception as e:
            log.warning("[API] connection lost")