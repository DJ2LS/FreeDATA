#!/usr/bin/env python3


import structlog
import threading
import websocket
import time

class TCICtrl:
    def __init__(self, audio_rx_q, hostname='127.0.0.1', port=50001):
        # websocket.enableTrace(True)
        self.log = structlog.get_logger("TCI")

        self.audio_received_queue = audio_rx_q

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
        self.crc = None
        self.channel = None

        self.frequency = None
        self.bandwidth = None
        self.mode = None
        self.alc = None
        self.meter = None
        self.level = None
        self.ptt = None

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
        # rel.signal(2, rel.abort)  # Keyboard Interrupt
        # rel.dispatch()

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
                self.channel = channel
                self.crc = crc

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


        if len(message)< 64:
            # find frequency
            if bytes(message, "utf-8").startswith(b"vfo:0,0,"):
                splitted_message = message.split("vfo:0,0,")
                self.frequency = splitted_message[1][:-1]

            # find mode
            if bytes(message, "utf-8").startswith(b"modulation:0,"):
                splitted_message = message.split("modulation:0,")
                self.mode = splitted_message[1][:-1]

                # find ptt
            #if bytes(message, "utf-8").startswith(b"trx:0,"):
            #    splitted_message = message.split("trx:0,")
            #    self.ptt = splitted_message[1][:-1]

            # find bandwidth
            #if message.startswith("rx_filter_band:0,"):
            #    splitted_message = message.split("rx_filter_band:0,")
            #    bandwidths = splitted_message[1]
            #    splitted_bandwidths = bandwidths.split(",")
            #    lower_bandwidth = int(splitted_bandwidths[0])
            #    upper_bandwidth = int(splitted_bandwidths[1][:-1])
            #    self.bandwidth = upper_bandwidth - lower_bandwidth





    def on_error(self, ws, error):
        self.log.error(
            "[TCI] Error FreeDATA to TCI rig!", ip=self.hostname, port=self.port, e=error
        )

    def on_close(self, ws, close_status_code, close_msg):
        self.log.warning(
            "[TCI] Closed FreeDATA to TCI connection!", ip=self.hostname, port=self.port, statu=close_status_code,
            msg=close_msg
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
        #print(data_out)

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

        while not self.tx_chrono:
            time.sleep(0.01)

        #print(len(data_out))
        #print(self.sample_rate)
        #print(self.audio_length)
        #print(self.channel)
        #print(self.crc)
        #print(self.codec)
        #print(self.tx_chrono)

        if self.tx_chrono:
            #print("#############")
            #print(len(data_out))
            #print(len(bytes(data_out)))
            #print("-------------")
            audio = bytearray(4096 + 64)

            audio[64:64 + len(bytes(data_out))] = bytes(data_out)
            audio[4:8] = self.sample_rate.to_bytes(4, byteorder='little', signed=False)
            # audio[8:12] = format.to_bytes(4,byteorder='little', signed=False)
            audio[12:16] = self.codec.to_bytes(4, byteorder='little', signed=False)
            audio[16:20] = self.crc.to_bytes(4, byteorder='little', signed=False)
            audio[20:24] = self.audio_length.to_bytes(4, byteorder='little', signed=False)
            audio[24:28] = int(2).to_bytes(4, byteorder='little', signed=False)
            audio[28:32] = self.channel.to_bytes(4, byteorder='little', signed=False)
            # audio[32:36] = reserved1.to_bytes(4,byteorder='little', signed=False)
            # audio[36:40] = reserved2.to_bytes(4,byteorder='little', signed=False)
            # audio[40:44] = reserved3.to_bytes(4,byteorder='little', signed=False)
            # audio[44:48] = reserved4.to_bytes(4,byteorder='little', signed=False)
            # audio[48:52] = reserved5.to_bytes(4,byteorder='little', signed=False)
            # audio[52:56] = reserved6.to_bytes(4,byteorder='little', signed=False)
            # audio[56:60] = reserved7.to_bytes(4,byteorder='little', signed=False)

            self.ws.send(audio, websocket.ABNF.OPCODE_BINARY)

    def set_ptt(self, state):
        if state:
            self.ws.send('trx:0,true,tci;')
        else:

            self.ws.send('trx:0,false;')
            self.tx_chrono = False

    def get_frequency(self):
        """ """
        self.ws.send('VFO:0,0;')
        return self.frequency

    def get_mode(self):
        """ """
        self.ws.send('MODULATION:0;')
        return self.mode

    def get_level(self):
        """ """
        return self.level

    def get_alc(self):
        """ """
        return self.alc

    def get_meter(self):
        """ """
        return self.meter

    def get_bandwidth(self):
        """ """
        return self.bandwidth

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
        self.ws.send(f'MODULATION:0,{str(mode)};')
        return None

    def set_frequency(self, frequency):
        """

        Args:
          frequency:

        Returns:

        """
        self.ws.send(f'VFO:0,0,{str(frequency)};')
        return None

    def get_status(self):
        """

        Args:
          mode:

        Returns:

        """
        return True

    def get_ptt(self):
        """ """
        self.ws.send('trx:0;')
        return self.ptt

    def close_rig(self):
        """ """
        return

    def wait_until_transmitted(self, txbuffer_out):
        duration = len(txbuffer_out) / 8000
        timestamp_to_sleep = time.time() + duration
        self.log.debug("[MDM] TCI calculated duration", duration=duration)
        tci_timeout_reached = False
        while not tci_timeout_reached:
            if self.radiocontrol in ["tci"]:
                if time.time() < timestamp_to_sleep:
                    tci_timeout_reached = False
                else:
                    tci_timeout_reached = True
            threading.Event().wait(0.01)
            # if we're transmitting FreeDATA signals, reset channel busy state