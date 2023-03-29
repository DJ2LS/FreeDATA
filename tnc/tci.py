#!/usr/bin/env python3


import structlog
import threading
import websocket
import numpy as np
from queues import AUDIO_TRANSMIT_QUEUE, AUDIO_RECEIVED_QUEUE

"""
trx:0,true;
trx:0,false;

"""

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

        # flag if we're receiving a tx_chrono
        self.tx_chrono = False

        # audio related parameters, will be updated by tx chrono
        self.sample_rate = None
        self.format = None
        self.codec = None
        self.audio_length = None


    def connect(self):
        self.log.info(
            "[TCI] Starting TCI thread!", ip=self.hostname, port=self.port
        )
        self.ws = websocket.WebSocketApp(
            f"ws://{self.hostname}:{self.port}",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

        self.ws.run_forever(reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if con>
        #rel.signal(2, rel.abort)  # Keyboard Interrupt
        #rel.dispatch()

    def on_message(self, ws, message):

        # ready message
        # we need to wait until radio is ready before we can push commands
        if message == "ready;":
            self.ws.send('audio_samplerate:8000;')
            self.ws.send('audio_stream_channels:1;')
            self.ws.send('audio_stream_sample_type:int16;')
            self.ws.send('audio_stream_samples:1200;')
            self.ws.send('audio_start:0;')

        # tx chrono frame
        if len(message) in {64}:
            receiver = message[:4]
            sample_rate = int.from_bytes(message[4:8], "little")
            format = int.from_bytes(message[8:12], "little")
            codec = int.from_bytes(message[12:16], "little")
            crc = int.from_bytes(message[16:20], "little")
            audio_length = int.from_bytes(message[20:24], "little")
            type = int.from_bytes(message[24:28], "little")
            channel = int.from_bytes(message[28:32], "little")
            reserved1 = int.from_bytes(message[32:36], "little")
            reserved2 = int.from_bytes(message[36:40], "little")
            reserved3 = int.from_bytes(message[40:44], "little")
            reserved4 = int.from_bytes(message[44:48], "little")
            reserved5 = int.from_bytes(message[48:52], "little")
            reserved6 = int.from_bytes(message[52:56], "little")
            reserved7 = int.from_bytes(message[56:60], "little")
            reserved8 = int.from_bytes(message[60:64], "little")
            if type == 3:
                self.tx_chrono = True

                self.sample_rate = sample_rate
                self.format = format
                self.codec = codec
                self.audio_length = audio_length

        # audio frame
        if len(message) in {576, 2464, 4160}:
            # audio received
            receiver = message[:4]
            sample_rate = int.from_bytes(message[4:8], "little")
            format = int.from_bytes(message[8:12], "little")
            codec = int.from_bytes(message[12:16], "little")
            crc = int.from_bytes(message[16:20], "little")
            audio_length = int.from_bytes(message[20:24], "little")
            type = int.from_bytes(message[24:28], "little")
            channel = int.from_bytes(message[28:32], "little")
            reserved1 = int.from_bytes(message[32:36], "little")
            reserved2 = int.from_bytes(message[36:40], "little")
            reserved3 = int.from_bytes(message[40:44], "little")
            reserved4 = int.from_bytes(message[44:48], "little")
            reserved5 = int.from_bytes(message[48:52], "little")
            reserved6 = int.from_bytes(message[52:56], "little")
            reserved7 = int.from_bytes(message[56:60], "little")
            reserved8 = int.from_bytes(message[60:64], "little")
            audio_data = message[64:]
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
        self.ws = ws
        self.log.info(
            "[TCI] Connected FreeDATA to TCI rig!", ip=self.hostname, port=self.port
        )


        self.log.info(
            "[TCI] Init...", ip=self.hostname, port=self.port
        )

    def push_audio(self, data_out):
        print(data_out)

        """
        # audio[:4] = receiver.to_bytes(4,byteorder='little', signed=False)
        audio[4:8] = sample_rate.to_bytes(4, byteorder='little', signed=False)
        audio[8:12] = format.to_bytes(4, byteorder='little', signed=False)
        audio[12:16] = codec.to_bytes(4, byteorder='little', signed=False)
        audio[16:20] = crc.to_bytes(4, byteorder='little', signed=False)
        audio[20:24] = audio_length.to_bytes(4, byteorder='little', signed=False)
        audio[24:28] = int(2).to_bytes(4, byteorder='little', signed=True)
        audio[28:32] = channel.to_bytes(4, byteorder='little', signed=False)
        audio[32:36] = reserved1.to_bytes(4, byteorder='little', signed=False)
        audio[36:40] = reserved2.to_bytes(4, byteorder='little', signed=False)
        audio[40:44] = reserved3.to_bytes(4, byteorder='little', signed=False)
        audio[44:48] = reserved4.to_bytes(4, byteorder='little', signed=False)
        audio[48:52] = reserved5.to_bytes(4, byteorder='little', signed=False)
        audio[52:56] = reserved6.to_bytes(4, byteorder='little', signed=False)
        audio[56:60] = reserved7.to_bytes(4, byteorder='little', signed=False)
        audio[60:64] = reserved8.to_bytes(4, byteorder='little', signed=False)
        """

        print(self.audio_length)
        print(self.tx_chrono)
        print(self.format)
        print(self.codec)

        if self.tx_chrono:
            # dummy for now ...
            audio = bytearray(4096 + 64)

            # generate sine wave
            rate = 8000  # samples per second
            T = 3  # sample duration (seconds)
            # n = int(rate*T)        # number of samples
            n = 1200
            t = np.arange(n) / rate  # grid of time values

            f = 440.0  # sound frequency (Hz)
            x = np.sin(2 * np.pi * f * t)

            # print(len(x))
            audio[64:] = bytes(x)
            audio[24:28] = int(2).to_bytes(4, byteorder='little', signed=True)
            self.ws.send(audio, websocket.ABNF.OPCODE_BINARY)

    def set_ptt(self, state):
        if state:
            self.ws.send('trx:0,true,tci;')
        else:
            self.ws.send('trx:0,false;')

    def get_frequency(self):
        """ """
        return None

    def get_mode(self):
        """ """
        return None

    def get_level(self):
        """ """
        return None

    def get_alc(self):
        """ """
        return None

    def get_meter(self):
        """ """
        return None

    def get_bandwidth(self):
        """ """
        return None

    def get_strength(self):
        """ """
        return None

    def set_bandwidth(self):
        """ """
        return None

    def set_mode(self, mode):
        """

        Args:
          mode:

        Returns:

        """
        return None

    def set_frequency(self, frequency):
        """

        Args:
          frequency:

        Returns:

        """
        return None

    def get_status(self):
        """

        Args:
          mode:

        Returns:

        """
        return "connected"

    def get_ptt(self):
        """ """
        return None

    def close_rig(self):
        """ """
        return
