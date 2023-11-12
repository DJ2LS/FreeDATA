# -*- coding: UTF-8 -*-
"""
Created on 05.11.23

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import requests
import ujson as json
import structlog
from global_instances import ARQ, HamlibParam, Station, Modem

log = structlog.get_logger("stats")


class stats():
    def __init__(self):
        self.explorer_url = "https://api.freedata.app/stats.php"

    def push(self, frame_nack_counter, status, duration):
        crcerror = status in ["crc_error", "wrong_crc"]
        # get avg snr
        try:
            snr_raw = [item["snr"] for item in ARQ.speed_list]
            avg_snr = round(sum(snr_raw) / len(snr_raw), 2 )
        except Exception:
            avg_snr = 0

        headers = {"Content-Type": "application/json"}
        station_data = {
            'callsign': str(Station.mycallsign, "utf-8"),
            'dxcallsign': str(Station.dxcallsign, "utf-8"),
            'gridsquare': str(Station.mygrid, "utf-8"),
            'dxgridsquare': str(Station.dxgrid, "utf-8"),
            'frequency': 0 if HamlibParam.hamlib_frequency is None else HamlibParam.hamlib_frequency,
            'avgstrength': 0,
            'avgsnr': avg_snr,
            'bytesperminute': ARQ.bytes_per_minute,
            'filesize': ARQ.total_bytes,
            'compressionfactor': ARQ.arq_compression_factor,
            'nacks': frame_nack_counter,
            'crcerror': crcerror,
            'duration': duration,
            'percentage': ARQ.arq_transmission_percent,
            'status': status,
            'version': Modem.version
        }

        station_data = json.dumps(station_data)
        print(station_data)
        try:
            response = requests.post(self.explorer_url, json=station_data, headers=headers)
            log.info("[STATS] push", code=response.status_code)

            # print(response.status_code)
            # print(response.content)

        except Exception as e:
            log.warning("[EXPLORER] connection lost")
