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

log = structlog.get_logger("stats")


class stats():
    def __init__(self):
        self.explorer_url = "https://api.freedata.app/stats.php"

    def push(self, frame_nack_counter, status, duration):
        crcerror = status in ["crc_error", "wrong_crc"]
        # get avg snr
        try:
            snr_raw = [item["snr"] for item in static.SPEED_LIST]
            avg_snr = round(sum(snr_raw) / len(snr_raw), 2 )
        except Exception:
            avg_snr = 0

        headers = {"Content-Type": "application/json"}
        station_data = {
            'callsign': str(static.MYCALLSIGN, "utf-8"),
            'dxcallsign': str(static.DXCALLSIGN, "utf-8"),
            'gridsquare': str(static.MYGRID, "utf-8"),
            'dxgridsquare': str(static.DXGRID, "utf-8"),
            'frequency': 0 if static.HAMLIB_FREQUENCY is None else static.HAMLIB_FREQUENCY,
            'avgstrength': 0,
            'avgsnr': avg_snr,
            'bytesperminute': static.ARQ_BYTES_PER_MINUTE,
            'filesize': static.TOTAL_BYTES,
            'compressionfactor': static.ARQ_COMPRESSION_FACTOR,
            'nacks': frame_nack_counter,
            'crcerror': crcerror,
            'duration': duration,
            'percentage': static.ARQ_TRANSMISSION_PERCENT,
            'status': status,
            'version': static.VERSION
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
