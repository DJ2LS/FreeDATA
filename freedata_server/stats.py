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


class stats():
    def __init__(self, config, event_queue, states):
        self.api_url = "https://api.freedata.app/stats.php"
        self.states = states

    def push(self, status, session_statistics):
        # get avg snr
        try:
            snr_raw = [item["snr"] for item in self.states.arq_speed_list]
            avg_snr = round(sum(snr_raw) / len(snr_raw), 2)
        except Exception:
            avg_snr = 0

        headers = {"Content-Type": "application/json"}
        station_data = {
            'callsign': str(self.states.mycallsign, "utf-8"),
            'dxcallsign': str(self.states.dxcallsign, "utf-8"),
            'gridsquare': str(self.states.mygrid, "utf-8"),
            'dxgridsquare': str(self.states.dxgrid, "utf-8"),
            'frequency': 0 if self.states.radio_frequency is None else self.states.radio_frequency,
            'avgsnr': avg_snr,
            'bytesperminute': session_statistics['bytes_per_minute'],
            'filesize': session_statistics['total_bytes'],
            'duration': session_statistics['duration'],
            'status': status,
            'version': self.states.modem_version,
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