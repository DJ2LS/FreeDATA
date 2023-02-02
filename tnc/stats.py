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
    def push(self):
        """
        $callsign = $json["callsign"];
        $dxcallsign = $json["dxcallsign"];
        $gridsquare = $json["gridsquare"];
        $dxgridsquare = $json["dxgridsquare"];
        $frequency = $json["frequency"];
        $avgstrength = $json["avgstrength"];
        $avgsnr = $json["avgsnr"];
        $bytesperminute = $json["bytesperminute"];
        $filesize = $json["filesize"];
        $compressionfactor = $json["compressionfactor"];
        $nacks = $json["nacks"];
        $crcerror = $json["crcerror"];
        $duration = $json["duration"];
        $version = $json["version"];
        """

        headers = {"Content-Type": "application/json"}
        station_data = {
            'callsign': str(static.MYCALLSIGN, "utf-8"),
            'dxcallsign': str(static.DXCALLSIGN, "utf-8"),
            'gridsquare': str(static.MYGRID, "utf-8"),
            'dxgridsquare': str(static.DXGRID, "utf-8"),
            'frequency': 0 if static.HAMLIB_FREQUENCY is None else static.HAMLIB_FREQUENCY,
            'avgstrength': 0,
            'avgsnr': 0,
            'bytesperminute': str(static.ARQ_BYTES_PER_MINUTE, "utf-8"),
            'filesize': str(static.TOTAL_BYTES, "utf-8"),
            'compressionfactor': str(static.ARQ_COMPRESSION_FACTOR, "utf-8"),
            'nacks': 0,
            'crcerror': 0,
            'duration': 0,
            'percentage': 0,
            'version': str(static.VERSION, "utf-8")
        }

        station_data = json.dumps(station_data)
        try:
            response = requests.post(self.explorer_url, json=station_data, headers=headers)
            log.info("[STATS] push", code=response.status_code)

            # print(response.status_code)
            # print(response.content)

        except Exception as e:
            log.warning("[EXPLORER] connection lost")
