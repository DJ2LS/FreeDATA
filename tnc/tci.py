#!/usr/bin/env python3
# class taken from darksidelemm
# rigctl - https://github.com/darksidelemm/rotctld-web-gui/blob/master/rotatorgui.py#L35
#
# modified and adjusted to FreeDATA needs by DJ2LS

import socket
import structlog
import threading
import static
import numpy as np
import websocket
import _thread
import time
import rel
from queues import AUDIO_TRANSMIT_QUEUE, AUDIO_RECEIVED_QUEUE



class TCI:
    def __init__(self, hostname='127.0.0.1', port=50001):
        # websocket.enableTrace(True)
        self.log = structlog.get_logger("TCI")

        self.audio_received_queue = AUDIO_RECEIVED_QUEUE
        self.audio_transmit_queue = AUDIO_TRANSMIT_QUEUE

        self.hostname = str(hostname)
        self.port = str(port)

        self.ws = ''

        tci_thread = threading.Thread(
            target=self.connect,
            name="TCI THREAD",
            daemon=True,
        )
        tci_thread.start()

    def connect(self):
        self.log.info(
            "[TCI] Starting TCI thread!", ip=self.hostname, port=self.port
        )
        self.ws = websocket.WebSocketApp("ws://" + self.hostname + ":" + self.port,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close
                                         )

        self.ws.run_forever(reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if con>
        #rel.signal(2, rel.abort)  # Keyboard Interrupt
        #rel.dispatch()

    def on_message(self, ws, message):
        if message == "ready;":
            self.ws.send('audio_samplerate:8000;')
            self.ws.send('audio_stream_channels:1;')
            self.ws.send('AUDIO_STREAM_SAMPLE_TYPE:int16;')
            self.ws.send('AUDIO_STREAM_SAMPLES:1200;')
            self.ws.send('audio_start:0;')

        if len(message) == 576 or len(message) == 2464 or len(message) == 4160:
            # audio received
            receiver = message[:4]
            sample_rate = int.from_bytes(message[4:8], "little")
            format = int.from_bytes(message[8:12], "little")
            codec = message[12:16]
            crc = message[16:20]
            audio_length = int.from_bytes(message[20:24], "little")
            type = int.from_bytes(message[24:28], "little")
            channel = int.from_bytes(message[28:32], "little")
            reserved = int.from_bytes(message[32:36], "little")
            audio_data = message[36+28:]
            self.audio_received_queue.put(audio_data)

    def on_error(self, error):
        self.log.error(
            "[TCI] Error FreeDATA to TCI rig!", ip=self.hostname, port=self.port, e=error
        )

    def on_close(self, ws, close_status_code, close_msg):
        self.log.warning(
            "[TCI] Closed FreeDATA to TCI connection!", ip=self.hostname, port=self.port, statu=close_status_code, msg=close_msg
        )

    def on_open(self, ws):
        self.log.info(
            "[TCI] Connected FreeDATA to TCI rig!", ip=self.hostname, port=self.port
        )


        self.log.info(
            "[TCI] Init...", ip=self.hostname, port=self.port
        )
