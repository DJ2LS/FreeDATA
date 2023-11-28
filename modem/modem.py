#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel

import atexit
import ctypes
import os
import queue
import threading
import time
from collections import deque
import codec2
import itertools
import numpy as np
import sounddevice as sd
import structlog
import tci
import cw
from queues import DATA_QUEUE_RECEIVED, MODEM_RECEIVED_QUEUE, MODEM_TRANSMIT_QUEUE, RIGCTLD_COMMAND_QUEUE, \
    AUDIO_RECEIVED_QUEUE, AUDIO_TRANSMIT_QUEUE, MESH_RECEIVED_QUEUE
import audio
import event_manager
from modem_frametypes import FRAME_TYPE
import beacon

TESTMODE = False
RXCHANNEL = ""
TXCHANNEL = ""

# Receive only specific modes to reduce CPU load
RECEIVE_SIG0 = True
RECEIVE_SIG1 = False
RECEIVE_DATAC1 = False
RECEIVE_DATAC3 = False
RECEIVE_DATAC4 = False


# state buffer

SIG0_DATAC13_STATE = []
SIG1_DATAC13_STATE = []
DAT0_DATAC1_STATE = []
DAT0_DATAC3_STATE = []
DAT0_DATAC4_STATE = []

FSK_LDPC0_STATE = []
FSK_LDPC1_STATE = []


class RF:
    """Class to encapsulate interactions between the audio device and codec2"""

    log = structlog.get_logger("RF")

    def __init__(self, config, event_queue, fft_queue, service_queue, states) -> None:
        self.config = config
        print(config)
        self.service_queue = service_queue
        self.states = states

        self.sampler_avg = 0
        self.buffer_avg = 0

        # these are crc ids now
        self.audio_input_device = config['AUDIO']['input_device']
        self.audio_output_device = config['AUDIO']['output_device']

        self.rx_audio_level = config['AUDIO']['rx_audio_level']
        self.tx_audio_level = config['AUDIO']['tx_audio_level']
        self.enable_audio_auto_tune = config['AUDIO']['enable_auto_tune']
        self.enable_fsk = config['MODEM']['enable_fsk']
        #Dynamically enable FFT data stream when a client connects to FFT web socket
        self.enable_fft_stream = False
        self.tx_delay = config['MODEM']['tx_delay']
        self.tuning_range_fmin = config['MODEM']['tuning_range_fmin']
        self.tuning_range_fmax = config['MODEM']['tuning_range_fmax']

        self.radiocontrol = config['RADIO']['control']
        self.rigctld_ip = config['RIGCTLD']['ip']
        self.rigctld_port = config['RIGCTLD']['port']

        self.states.setTransmitting(False)

        self.ptt_state = False
        self.radio_alc = 0.0

        self.tci_ip = config['TCI']['tci_ip']
        self.tci_port = config['TCI']['tci_port']

        self.buffer_overflow_counter = [0, 0, 0, 0, 0, 0, 0, 0]

        self.channel_busy_delay = 0

        self.AUDIO_SAMPLE_RATE_RX = 48000
        self.AUDIO_SAMPLE_RATE_TX = 48000
        self.MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000

        self.AUDIO_FRAMES_PER_BUFFER_RX = 2400 * 2  # 8192
        # 8192 Let's do some tests with very small chunks for TX
        self.AUDIO_FRAMES_PER_BUFFER_TX = 1200 if self.radiocontrol in ["tci"] else 2400 * 2
        # 8 * (self.AUDIO_SAMPLE_RATE_RX/self.MODEM_SAMPLE_RATE) == 48
        self.AUDIO_CHANNELS = 1
        self.MODE = 0

        self.is_codec2_traffic_cooldown = 20
        self.is_codec2_traffic_counter = 0
        # Locking state for mod out so buffer will be filled before we can use it
        # https://github.com/DJ2LS/FreeDATA/issues/127
        # https://github.com/DJ2LS/FreeDATA/issues/99
        self.mod_out_locked = True

        # Make sure our resampler will work
        assert (self.AUDIO_SAMPLE_RATE_RX / self.MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48  # type: ignore


        self.modem_transmit_queue = MODEM_TRANSMIT_QUEUE
        self.modem_received_queue = MODEM_RECEIVED_QUEUE

        self.audio_received_queue = AUDIO_RECEIVED_QUEUE
        self.audio_transmit_queue = AUDIO_TRANSMIT_QUEUE

        # Init FIFO queue to store modulation out in
        self.modoutqueue = deque()

        self.event_manager = event_manager.EventManager([event_queue])

        self.fft_queue = fft_queue

        self.beacon = beacon.Beacon(self.config, self.states, event_queue, 
                                    self.log, MODEM_TRANSMIT_QUEUE)

        self.start_modem()


    # --------------------------------------------------------------------------------------------------------
    def tci_tx_callback(self) -> None:
        """
        Callback for TCI TX
        """
        while True:
            threading.Event().wait(0.01)

            if len(self.modoutqueue) > 0 and not self.mod_out_locked:
                self.radio.set_ptt(True)
                self.event_manager.send_ptt_change(True)

                data_out = self.modoutqueue.popleft()
                self.tci_module.push_audio(data_out)

    def start_modem(self):
        if not TESTMODE and self.radiocontrol not in ["tci"]:
            result = self.init_audio()

        elif not TESTMODE:
            result = self.init_tci()
        else:
            result = self.init_mkfifo()
        if result not in [False]:
            # init codec2 instances
            self.init_codec2()

            # init rig control
            self.init_rig_control()

            # init decoders
            self.init_decoders()

            # init decoding threads
            self.init_data_threads()
            atexit.register(self.stream.stop)

            # init beacon
            self.beacon.start()
        else:
            return False

    def stop_modem(self):
        try:
            # let's stop the modem service
            self.service_queue.put("stop")
            # simulate audio class active state for reducing cli output
            # self.stream = lambda: None
            # self.stream.active = False
            # self.stream.stop

            self.beacon.stop()

        except Exception:
            self.log.error("[MDM] Error stopping modem")

    def init_audio(self):
        self.log.info(f"[MDM] init: get audio devices", input_device=self.audio_input_device,
                      output_device=self.audio_output_device)
        try:
            result = audio.get_device_index_from_crc(self.audio_input_device, True)
            if result is None:
                raise ValueError("Invalid input device")
            else:
                in_dev_index, in_dev_name = result

            result = audio.get_device_index_from_crc(self.audio_output_device, False)
            if result is None:
                raise ValueError("Invalid output device")
            else:
                out_dev_index, out_dev_name = result

            self.log.info(f"[MDM] init: receiving audio from '{in_dev_name}'")
            self.log.info(f"[MDM] init: transmiting audio on '{out_dev_name}'")
            self.log.debug("[MDM] init: starting pyaudio callback and decoding threads")

            # init codec2 resampler
            self.resampler = codec2.resampler()

            # init audio stream
            self.stream = sd.RawStream(
                channels=1,
                dtype="int16",
                callback=self.callback,
                device=(in_dev_index, out_dev_index),
                samplerate=self.AUDIO_SAMPLE_RATE_RX,
                blocksize=4800,
            )
            self.stream.start()
            return True



        except Exception as audioerr:
            self.log.error("[MDM] init: starting pyaudio callback failed", e=audioerr)
            self.stop_modem()
            return False


    def init_tci(self):
        # placeholder area for processing audio via TCI
        # https://github.com/maksimus1210/TCI
        self.log.warning("[MDM] [TCI] Not yet fully implemented", ip=self.tci_ip, port=self.tci_port)

        # we are trying this by simulating an audio stream Object like with mkfifo
        class Object:
            """An object for simulating audio stream"""
            active = True

        self.stream = Object()

        # lets init TCI module
        self.tci_module = tci.TCICtrl()

        tci_rx_callback_thread = threading.Thread(
            target=self.tci_rx_callback,
            name="TCI RX CALLBACK THREAD",
            daemon=True,
        )
        tci_rx_callback_thread.start()

        # let's start the audio tx callback
        self.log.debug("[MDM] Starting tci tx callback thread")
        tci_tx_callback_thread = threading.Thread(
            target=self.tci_tx_callback,
            name="TCI TX CALLBACK THREAD",
            daemon=True,
        )
        tci_tx_callback_thread.start()
    def init_mkfifo(self):
        class Object:
            """An object for simulating audio stream"""
            active = True

        self.stream = Object()

        # Create mkfifo buffers
        try:
            os.mkfifo(RXCHANNEL)
            os.mkfifo(TXCHANNEL)
        except Exception as err:
            self.log.info(f"[MDM] init:mkfifo: Exception: {err}")

        mkfifo_write_callback_thread = threading.Thread(
            target=self.mkfifo_write_callback,
            name="MKFIFO WRITE CALLBACK THREAD",
            daemon=True,
        )
        mkfifo_write_callback_thread.start()

        self.log.debug("[MDM] Starting mkfifo_read_callback")
        mkfifo_read_callback_thread = threading.Thread(
            target=self.mkfifo_read_callback,
            name="MKFIFO READ CALLBACK THREAD",
            daemon=True,
        )
        mkfifo_read_callback_thread.start()


    def tci_rx_callback(self) -> None:
        """
        Callback for TCI RX

        data_in48k must be filled with 48000Hz audio raw data

        """

        while True:

            x = self.audio_received_queue.get()
            x = np.frombuffer(x, dtype=np.int16)
            # x = self.resampler.resample48_to_8(x)
            
            self.calculate_fft(x)

            length_x = len(x)
            for data_buffer, receive in [
                (self.sig0_datac13_buffer, RECEIVE_SIG0),
                (self.sig1_datac13_buffer, RECEIVE_SIG1),
                (self.dat0_datac1_buffer, RECEIVE_DATAC1),
                (self.dat0_datac3_buffer, RECEIVE_DATAC3),
                (self.dat0_datac4_buffer, RECEIVE_DATAC4),
                (self.fsk_ldpc_buffer_0, self.enable_fsk),
                (self.fsk_ldpc_buffer_1, self.enable_fsk),
            ]:
                if (
                        not (data_buffer.nbuffer + length_x) > data_buffer.size
                        and receive
                ):
                    data_buffer.push(x)

    def mkfifo_read_callback(self) -> None:
        """
        Support testing by reading the audio data from a pipe and
        depositing the data into the codec data buffers.
        """
        while True:
            threading.Event().wait(0.01)
            # -----read
            data_in48k = bytes()
            with open(RXCHANNEL, "rb") as fifo:
                for line in fifo:
                    data_in48k += line

                    while len(data_in48k) >= 48:
                        x = np.frombuffer(data_in48k[:48], dtype=np.int16)
                        x = self.resampler.resample48_to_8(x)
                        data_in48k = data_in48k[48:]

                        length_x = len(x)
                        for data_buffer, receive in [
                            (self.sig0_datac13_buffer, RECEIVE_SIG0),
                            (self.sig1_datac13_buffer, RECEIVE_SIG1),
                            (self.dat0_datac1_buffer, RECEIVE_DATAC1),
                            (self.dat0_datac3_buffer, RECEIVE_DATAC3),
                            (self.dat0_datac4_buffer, RECEIVE_DATAC4),
                            (self.fsk_ldpc_buffer_0, self.enable_fsk),
                            (self.fsk_ldpc_buffer_1, self.enable_fsk),
                        ]:
                            if (
                                    not (data_buffer.nbuffer + length_x) > data_buffer.size
                                    and receive
                            ):
                                data_buffer.push(x)

    def mkfifo_write_callback(self) -> None:
        """Support testing by writing the audio data to a pipe."""
        while True:
            threading.Event().wait(0.01)

            # -----write
            if len(self.modoutqueue) > 0 and not self.mod_out_locked:
                data_out48k = self.modoutqueue.popleft()
                # print(len(data_out48k))

                with open(TXCHANNEL, "wb") as fifo_write:
                    fifo_write.write(data_out48k)
                    fifo_write.flush()
                    fifo_write.flush()

    # Callback for the audio streaming devices
    def callback(self, data_in48k, outdata, frames, time, status) -> None:
        """
        Receive data into appropriate queue.

        Args:
            data_in48k: Incoming data received
            outdata: Container for the data returned
            frames: Number of frames
            time:
          status:

        """
        # self.log.debug("[MDM] callback")
        try:
            x = np.frombuffer(data_in48k, dtype=np.int16)
            x = self.resampler.resample48_to_8(x)
            x = set_audio_volume(x, self.rx_audio_level)

            # audio recording for debugging purposes
            # TODO Find a nice place for this
            #if AudioParam.audio_record:
            #    AudioParam.audio_record_file.writeframes(x)

            # Avoid decoding when transmitting to reduce CPU
            # TODO Overriding this for testing purposes
            # if not self.states.is_transmitting:
            length_x = len(x)
            # Avoid buffer overflow by filling only if buffer for
            # selected datachannel mode is not full
            for audiobuffer, receive, index in [
                (self.sig0_datac13_buffer, RECEIVE_SIG0, 0),
                (self.sig1_datac13_buffer, RECEIVE_SIG1, 1),
                (self.dat0_datac1_buffer, RECEIVE_DATAC1, 2),
                (self.dat0_datac3_buffer, RECEIVE_DATAC3, 3),
                (self.dat0_datac4_buffer, RECEIVE_DATAC4, 4),
                (self.fsk_ldpc_buffer_0, self.enable_fsk, 5),
                (self.fsk_ldpc_buffer_1, self.enable_fsk, 6),
            ]:
                if (audiobuffer.nbuffer + length_x) > audiobuffer.size:
                    self.buffer_overflow_counter[index] += 1
                    self.event_manager.send_buffer_overflow(self.buffer_overflow_counter)
                elif receive:
                    audiobuffer.push(x)
            # end of "not self.states.is_transmitting" if block

            if not self.modoutqueue or self.mod_out_locked:
                data_out48k = np.zeros(frames, dtype=np.int16)
                self.calculate_fft(x)
            else:
                # TODO Moved to this place for testing
                # Maybe we can avoid moments of silence before transmitting
                self.radio.set_ptt(True)
                self.event_manager.send_ptt_change(True)

                data_out48k = self.modoutqueue.popleft()
                self.calculate_fft(data_out48k)
        except Exception as e:
            self.log.warning(f"[MDM] audio callback not ready yet: {e}")

        try:
            outdata[:] = data_out48k[:frames]
        except IndexError as err:
            self.log.debug(f"[MDM] callback writing error: IndexError: {err}")

        # return (data_out48k, audio.pyaudio.paContinue)

    # --------------------------------------------------------------------
    def transmit(
            self, mode, repeats: int, repeat_delay: int, frames: bytearray
    ) -> bool:
        """

        Args:
          mode:
          repeats:
          repeat_delay:
          frames:

        """
        self.reset_data_sync()

        if mode == codec2.FREEDV_MODE.datac0.value:
            freedv = self.freedv_datac0_tx
        elif mode == codec2.FREEDV_MODE.datac1.value:
            freedv = self.freedv_datac1_tx
        elif mode == codec2.FREEDV_MODE.datac3.value:
            freedv = self.freedv_datac3_tx
        elif mode == codec2.FREEDV_MODE.datac4.value:
            freedv = self.freedv_datac4_tx
        elif mode == codec2.FREEDV_MODE.datac13.value:
            freedv = self.freedv_datac13_tx
        elif mode == codec2.FREEDV_MODE.fsk_ldpc_0.value:
            freedv = self.freedv_ldpc0_tx
        elif mode == codec2.FREEDV_MODE.fsk_ldpc_1.value:
            freedv = self.freedv_ldpc1_tx
        else:
            return False

        # Wait for some other thread that might be transmitting
        self.states.waitForTransmission()
        self.states.setTransmitting(True)
        # if we're transmitting FreeDATA signals, reset channel busy state
        self.states.set("channel_busy", False)

        start_of_transmission = time.time()
        # TODO Moved ptt toggle some steps before audio is ready for testing
        # Toggle ptt early to save some time and send ptt state via socket
        # self.radio.set_ptt(True)
        # jsondata = {"ptt": "True"}
        # data_out = json.dumps(jsondata)
        # sock.SOCKET_QUEUE.put(data_out)

        # Open codec2 instance
        self.MODE = mode

        # Get number of bytes per frame for mode
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_bytes_per_frame = bytes_per_frame - 2

        # Init buffer for data
        n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
        mod_out = ctypes.create_string_buffer(n_tx_modem_samples * 2)

        # Init buffer for preample
        n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(
            freedv
        )
        mod_out_preamble = ctypes.create_string_buffer(n_tx_preamble_modem_samples * 2)

        # Init buffer for postamble
        n_tx_postamble_modem_samples = (
            codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
        )
        mod_out_postamble = ctypes.create_string_buffer(
            n_tx_postamble_modem_samples * 2
        )

        # Add empty data to handle ptt toggle time
        if self.tx_delay > 0:
            data_delay = int(self.MODEM_SAMPLE_RATE * (self.tx_delay / 1000))  # type: ignore
            mod_out_silence = ctypes.create_string_buffer(data_delay * 2)
            txbuffer = bytes(mod_out_silence)
        else:
            txbuffer = bytes()

        self.log.debug(
            "[MDM] TRANSMIT", mode=self.MODE, payload=payload_bytes_per_frame, delay=self.tx_delay
        )

        for _ in range(repeats):

            # Create modulation for all frames in the list
            for frame in frames:
                # Write preamble to txbuffer
                # codec2 fsk preamble may be broken -
                # at least it sounds like that, so we are disabling it for testing
                if self.MODE not in [
                    codec2.FREEDV_MODE.fsk_ldpc_0.value,
                    codec2.FREEDV_MODE.fsk_ldpc_1.value,
                ]:
                    # Write preamble to txbuffer
                    codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
                    txbuffer += bytes(mod_out_preamble)

                # Create buffer for data
                # Use this if CRC16 checksum is required (DATAc1-3)
                buffer = bytearray(payload_bytes_per_frame)
                # Set buffersize to length of data which will be send
                buffer[: len(frame)] = frame  # type: ignore

                # Create crc for data frame -
                #   Use the crc function shipped with codec2
                #   to avoid CRC algorithm incompatibilities
                # Generate CRC16
                crc = ctypes.c_ushort(
                    codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame)
                )
                # Convert crc to 2-byte (16-bit) hex string
                crc = crc.value.to_bytes(2, byteorder="big")
                # Append CRC to data buffer
                buffer += crc

                data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
                # modulate DATA and save it into mod_out pointer
                codec2.api.freedv_rawdatatx(freedv, mod_out, data)
                txbuffer += bytes(mod_out)

                # codec2 fsk postamble may be broken -
                # at least it sounds like that, so we are disabling it for testing
                if self.MODE not in [
                    codec2.FREEDV_MODE.fsk_ldpc_0.value,
                    codec2.FREEDV_MODE.fsk_ldpc_1.value,
                ]:
                    # Write postamble to txbuffer
                    codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
                    # Append postamble to txbuffer
                    txbuffer += bytes(mod_out_postamble)

            # Add delay to end of frames
            samples_delay = int(self.MODEM_SAMPLE_RATE * (repeat_delay / 1000))  # type: ignore
            mod_out_silence = ctypes.create_string_buffer(samples_delay * 2)
            txbuffer += bytes(mod_out_silence)

        # Re-sample back up to 48k (resampler works on np.int16)
        x = np.frombuffer(txbuffer, dtype=np.int16)

        self.audio_auto_tune()
        x = set_audio_volume(x, self.tx_audio_level)

        if not self.radiocontrol in ["tci"]:
            txbuffer_out = self.resampler.resample8_to_48(x)
        else:
            txbuffer_out = x

        # Explicitly lock our usage of mod_out_queue if needed
        # This could avoid audio problems on slower CPU
        # we will fill our modout list with all data, then start
        # processing it in audio callback
        self.mod_out_locked = True

        # -------------------------------
        # add modulation to modout_queue
        self.enqueue_modulation(txbuffer_out)

        # Release our mod_out_lock, so we can use the queue
        self.mod_out_locked = False

        # we need to wait manually for tci processing
        if self.radiocontrol in ["tci"]:
            duration = len(txbuffer_out) / 8000
            timestamp_to_sleep = time.time() + duration
            self.log.debug("[MDM] TCI calculated duration", duration=duration)
            tci_timeout_reached = False
            #while time.time() < timestamp_to_sleep:
            #    threading.Event().wait(0.01)
        else:
            timestamp_to_sleep = time.time()
            # set tci timeout reached to True for overriding if not used
            tci_timeout_reached = True

        while self.modoutqueue or not tci_timeout_reached:
            if self.radiocontrol in ["tci"]:
                if time.time() < timestamp_to_sleep:
                    tci_timeout_reached = False
                else:
                    tci_timeout_reached = True
            threading.Event().wait(0.01)
            # if we're transmitting FreeDATA signals, reset channel busy state
            self.states.set("channel_busy", False)

        self.radio.set_ptt(False)

        # Push ptt state to socket stream
        self.event_manager.send_ptt_change(False)

        # After processing, set the locking state back to true to be prepared for next transmission
        self.mod_out_locked = True

        self.modem_transmit_queue.task_done()
        self.states.setTransmitting(False)

        end_of_transmission = time.time()
        transmission_time = end_of_transmission - start_of_transmission
        self.log.debug("[MDM] ON AIR TIME", time=transmission_time)

    def audio_auto_tune(self):
        # enable / disable AUDIO TUNE Feature / ALC correction
        if self.enable_audio_auto_tune:
            if self.radio_alc == 0.0:
                self.tx_audio_level = self.tx_audio_level + 20
            elif 0.0 < self.radio_alc <= 0.1:
                print("0.0 < self.radio_alc <= 0.1")
                self.tx_audio_level = self.tx_audio_level + 2
                self.log.debug("[MDM] AUDIO TUNE", audio_level=str(self.tx_audio_level),
                               alc_level=str(self.radio_alc))
            elif 0.1 < self.radio_alc < 0.2:
                print("0.1 < self.radio_alc < 0.2")
                self.tx_audio_level = self.tx_audio_level
                self.log.debug("[MDM] AUDIO TUNE", audio_level=str(self.tx_audio_level),
                               alc_level=str(self.radio_alc))
            elif 0.2 < self.radio_alc < 0.99:
                print("0.2 < self.radio_alc < 0.99")
                self.tx_audio_level = self.tx_audio_level - 20
                self.log.debug("[MDM] AUDIO TUNE", audio_level=str(self.tx_audio_level),
                               alc_level=str(self.radio_alc))
            elif 1.0 >= self.radio_alc:
                print("1.0 >= self.radio_alc")
                self.tx_audio_level = self.tx_audio_level - 40
                self.log.debug("[MDM] AUDIO TUNE", audio_level=str(self.tx_audio_level),
                               alc_level=str(self.radio_alc))
            else:
                self.log.debug("[MDM] AUDIO TUNE", audio_level=str(self.tx_audio_level),
                               alc_level=str(self.radio_alc))

    def transmit_morse(self, repeats, repeat_delay, frames):
        self.states.waitForTransmission()
        self.states.setTransmitting(True)
        # if we're transmitting FreeDATA signals, reset channel busy state
        self.states.set("channel_busy", False)
        self.log.debug(
            "[MDM] TRANSMIT", mode="MORSE"
        )
        start_of_transmission = time.time()

        txbuffer_out = cw.MorseCodePlayer().text_to_signal("DJ2LS-1")

        self.mod_out_locked = True
        self.enqueue_modulation(txbuffer_out)
        self.mod_out_locked = False

        # we need to wait manually for tci processing
        if self.radiocontrol in ["tci"]:
            duration = len(txbuffer_out) / 8000
            timestamp_to_sleep = time.time() + duration
            self.log.debug("[MDM] TCI calculated duration", duration=duration)
            tci_timeout_reached = False
            #while time.time() < timestamp_to_sleep:
            #    threading.Event().wait(0.01)
        else:
            timestamp_to_sleep = time.time()
            # set tci timeout reached to True for overriding if not used
            tci_timeout_reached = True

        while self.modoutqueue or not tci_timeout_reached:
            if self.radiocontrol in ["tci"]:
                if time.time() < timestamp_to_sleep:
                    tci_timeout_reached = False
                else:
                    tci_timeout_reached = True

            threading.Event().wait(0.01)
            # if we're transmitting FreeDATA signals, reset channel busy state
            self.states.set("channel_busy", False)

        self.radio.set_ptt(False)

        # Push ptt state to socket stream
        self.event_manager.send_ptt_change(False)

        # After processing, set the locking state back to true to be prepared for next transmission
        self.mod_out_locked = True

        self.modem_transmit_queue.task_done()
        self.states.setTransmitting(False)

        end_of_transmission = time.time()
        transmission_time = end_of_transmission - start_of_transmission
        self.log.debug("[MDM] ON AIR TIME", time=transmission_time)

    def enqueue_modulation(self, txbuffer_out):


        chunk_length = self.AUDIO_FRAMES_PER_BUFFER_TX  # 4800
        chunk = [
            txbuffer_out[i: i + chunk_length]
            for i in range(0, len(txbuffer_out), chunk_length)
        ]
        for c in chunk:
            # Pad the chunk, if needed
            if len(c) < chunk_length:
                delta = chunk_length - len(c)
                delta_zeros = np.zeros(delta, dtype=np.int16)
                c = np.append(c, delta_zeros)
                # self.log.debug("[MDM] mod out shorter than audio buffer", delta=delta)
            self.modoutqueue.append(c)

    def init_decoders(self):

        if self.enable_fsk:
            audio_thread_fsk_ldpc0 = threading.Thread(
                target=self.audio_fsk_ldpc_0, name="AUDIO_THREAD FSK LDPC0", daemon=True
            )
            audio_thread_fsk_ldpc0.start()

            audio_thread_fsk_ldpc1 = threading.Thread(
                target=self.audio_fsk_ldpc_1, name="AUDIO_THREAD FSK LDPC1", daemon=True
            )
            audio_thread_fsk_ldpc1.start()

        else:
            audio_thread_sig0_datac13 = threading.Thread(
                target=self.audio_sig0_datac13, name="AUDIO_THREAD DATAC13 - 0", daemon=True
            )
            audio_thread_sig0_datac13.start()

            audio_thread_sig1_datac13 = threading.Thread(
                target=self.audio_sig1_datac13, name="AUDIO_THREAD DATAC13 - 1", daemon=True
            )
            audio_thread_sig1_datac13.start()

            audio_thread_dat0_datac1 = threading.Thread(
                target=self.audio_dat0_datac1, name="AUDIO_THREAD DATAC1", daemon=True
            )
            audio_thread_dat0_datac1.start()

            audio_thread_dat0_datac3 = threading.Thread(
                target=self.audio_dat0_datac3, name="AUDIO_THREAD DATAC3", daemon=True
            )
            audio_thread_dat0_datac3.start()

            audio_thread_dat0_datac4 = threading.Thread(
                target=self.audio_dat0_datac4, name="AUDIO_THREAD DATAC4", daemon=True
            )
            audio_thread_dat0_datac4.start()

    def demodulate_audio(
            self,
            audiobuffer: codec2.audio_buffer,
            nin: int,
            freedv: ctypes.c_void_p,
            bytes_out,
            bytes_per_frame,
            state_buffer,
            mode_name,
    ) -> int:
        """
        De-modulate supplied audio stream with supplied codec2 instance.
        Decoded audio is placed into `bytes_out`.

        :param audiobuffer: Incoming audio
        :type audiobuffer: codec2.audio_buffer
        :param nin: Number of frames codec2 is expecting
        :type nin: int
        :param freedv: codec2 instance
        :type freedv: ctypes.c_void_p
        :param bytes_out: Demodulated audio
        :type bytes_out: _type_
        :param bytes_per_frame: Number of bytes per frame
        :type bytes_per_frame: int
        :param state_buffer: modem states
        :type state_buffer: int
        :param mode_name: mode name
        :type mode_name: str
        :return: NIN from freedv instance
        :rtype: int
        """

        nbytes = 0
        try:
            while self.stream.active:
                threading.Event().wait(0.01)
                while audiobuffer.nbuffer >= nin:
                    # demodulate audio
                    nbytes = codec2.api.freedv_rawdatarx(
                        freedv, bytes_out, audiobuffer.buffer.ctypes
                    )
                    # get current modem states and write to list
                    # 1 trial
                    # 2 sync
                    # 3 trial sync
                    # 6 decoded
                    # 10 error decoding == NACK
                    rx_status = codec2.api.freedv_get_rx_status(freedv)

                    if rx_status not in [0]:
                        # we need to disable this if in testmode as its causing problems with FIFO it seems
                        if not TESTMODE:
                            self.states.set("is_codec2_traffic", True)
                            self.is_codec2_traffic_counter = self.is_codec2_traffic_cooldown
                            if not self.states.channel_busy:
                                self.log.debug("[MDM] Setting channel_busy since codec2 data detected")
                                self.states.set("channel_busy", True)
                                self.channel_busy_delay += 10
                        self.log.debug(
                            "[MDM] [demod_audio] modem state", mode=mode_name, rx_status=rx_status,
                            sync_flag=codec2.api.rx_sync_flags_to_text[rx_status]
                        )
                    else:
                        self.states.set("is_codec2_traffic", False)

                    # decrement codec traffic counter for making state smoother
                    if self.is_codec2_traffic_counter > 0:
                        self.is_codec2_traffic_counter -= 1
                        self.states.set("is_codec2_traffic", True)
                    else:
                        self.states.set("is_codec2_traffic", False)

                    if rx_status == 10:
                        state_buffer.append(rx_status)

                    audiobuffer.pop(nin)
                    nin = codec2.api.freedv_nin(freedv)
                    if nbytes == bytes_per_frame:
                        print(bytes(bytes_out))

                        # ignore data channel opener frames for avoiding toggle states
                        # use case: opener already received, but ack got lost and we are receiving
                        # an opener again
                        if mode_name in ["sig1-datac13"] and int.from_bytes(bytes(bytes_out[:1]), "big") in [
                            FRAME_TYPE.ARQ_SESSION_OPEN.value,
                            FRAME_TYPE.ARQ_DC_OPEN_W.value,
                            FRAME_TYPE.ARQ_DC_OPEN_ACK_W.value,
                            FRAME_TYPE.ARQ_DC_OPEN_N.value,
                            FRAME_TYPE.ARQ_DC_OPEN_ACK_N.value
                        ]:
                            print("dropp")
                        elif int.from_bytes(bytes(bytes_out[:1]), "big") in [
                            FRAME_TYPE.MESH_BROADCAST.value,
                            FRAME_TYPE.MESH_SIGNALLING_PING.value,
                            FRAME_TYPE.MESH_SIGNALLING_PING_ACK.value,
                        ]:
                            self.log.debug(
                                "[MDM] [demod_audio] moving data to mesh dispatcher", nbytes=nbytes
                            )
                            MESH_RECEIVED_QUEUE.put([bytes(bytes_out), snr])

                        else:
                            self.log.debug(
                                "[MDM] [demod_audio] Pushing received data to received_queue", nbytes=nbytes
                            )
                            snr = self.calculate_snr(freedv)
                            self.modem_received_queue.put([bytes_out, freedv, bytes_per_frame, snr])
                            self.get_scatter(freedv)
                            state_buffer = []

        except Exception as e:
            self.log.warning("[MDM] [demod_audio] Stream not active anymore", e=e)

        return nin

    def init_codec2(self):
        # Open codec2 instances

        # DATAC13
        # SIGNALLING MODE 0 - Used for Connecting - Payload 14 Bytes
        self.sig0_datac13_freedv, \
                self.sig0_datac13_bytes_per_frame, \
                self.sig0_datac13_bytes_out, \
                self.sig0_datac13_buffer, \
                self.sig0_datac13_nin = \
                self.init_codec2_mode(codec2.FREEDV_MODE.datac13.value, None)

        # DATAC13
        # SIGNALLING MODE 1 - Used for ACK/NACK - Payload 5 Bytes
        self.sig1_datac13_freedv, \
                self.sig1_datac13_bytes_per_frame, \
                self.sig1_datac13_bytes_out, \
                self.sig1_datac13_buffer, \
                self.sig1_datac13_nin = \
                self.init_codec2_mode(codec2.FREEDV_MODE.datac13.value, None)

        # DATAC1
        self.dat0_datac1_freedv, \
                self.dat0_datac1_bytes_per_frame, \
                self.dat0_datac1_bytes_out, \
                self.dat0_datac1_buffer, \
                self.dat0_datac1_nin = \
                self.init_codec2_mode(codec2.FREEDV_MODE.datac1.value, None)

        # DATAC3
        self.dat0_datac3_freedv, \
                self.dat0_datac3_bytes_per_frame, \
                self.dat0_datac3_bytes_out, \
                self.dat0_datac3_buffer, \
                self.dat0_datac3_nin = \
                self.init_codec2_mode(codec2.FREEDV_MODE.datac3.value, None)

        # DATAC4
        self.dat0_datac4_freedv, \
                self.dat0_datac4_bytes_per_frame, \
                self.dat0_datac4_bytes_out, \
                self.dat0_datac4_buffer, \
                self.dat0_datac4_nin = \
                self.init_codec2_mode(codec2.FREEDV_MODE.datac4.value, None)


        # FSK LDPC - 0
        self.fsk_ldpc_freedv_0, \
                self.fsk_ldpc_bytes_per_frame_0, \
                self.fsk_ldpc_bytes_out_0, \
                self.fsk_ldpc_buffer_0, \
                self.fsk_ldpc_nin_0 = \
                self.init_codec2_mode(
                codec2.FREEDV_MODE.fsk_ldpc.value,
                codec2.api.FREEDV_MODE_FSK_LDPC_0_ADV
            )

        # FSK LDPC - 1
        self.fsk_ldpc_freedv_1, \
                self.fsk_ldpc_bytes_per_frame_1, \
                self.fsk_ldpc_bytes_out_1, \
                self.fsk_ldpc_buffer_1, \
                self.fsk_ldpc_nin_1 = \
                self.init_codec2_mode(
                codec2.FREEDV_MODE.fsk_ldpc.value,
                codec2.api.FREEDV_MODE_FSK_LDPC_1_ADV
            )

        # INIT TX MODES - here we need all modes. 
        self.freedv_datac0_tx = codec2.open_instance(codec2.FREEDV_MODE.datac0.value)
        self.freedv_datac1_tx = codec2.open_instance(codec2.FREEDV_MODE.datac1.value)
        self.freedv_datac3_tx = codec2.open_instance(codec2.FREEDV_MODE.datac3.value)
        self.freedv_datac4_tx = codec2.open_instance(codec2.FREEDV_MODE.datac4.value)
        self.freedv_datac13_tx = codec2.open_instance(codec2.FREEDV_MODE.datac13.value)
        self.freedv_ldpc0_tx = codec2.open_instance(codec2.FREEDV_MODE.fsk_ldpc_0.value)
        self.freedv_ldpc1_tx = codec2.open_instance(codec2.FREEDV_MODE.fsk_ldpc_1.value)

    def init_codec2_mode(self, mode, adv):
        """
        Init codec2 and return some important parameters

        Args:
          self:
          mode:
          adv:

        Returns:
            c2instance, bytes_per_frame, bytes_out, audio_buffer, nin
        """
        if adv:
            # FSK Long-distance Parity Code 1 - data frames
            c2instance = ctypes.cast(
                codec2.api.freedv_open_advanced(
                    codec2.FREEDV_MODE.fsk_ldpc.value,
                    ctypes.byref(adv),
                ),
                ctypes.c_void_p,
            )
        else:

            # create codec2 instance
            c2instance = ctypes.cast(
                codec2.api.freedv_open(mode), ctypes.c_void_p
            )

        # set tuning range
        codec2.api.freedv_set_tuning_range(
            c2instance,
            ctypes.c_float(float(self.tuning_range_fmin)),
            ctypes.c_float(float(self.tuning_range_fmax)),
        )

        # get bytes per frame
        bytes_per_frame = int(
            codec2.api.freedv_get_bits_per_modem_frame(c2instance) / 8
        )

        # create byte out buffer
        bytes_out = ctypes.create_string_buffer(bytes_per_frame)

        # set initial frames per burst
        codec2.api.freedv_set_frames_per_burst(c2instance, 1)

        # init audio buffer
        audio_buffer = codec2.audio_buffer(2 * self.AUDIO_FRAMES_PER_BUFFER_RX)

        # get initial nin
        nin = codec2.api.freedv_nin(c2instance)

        # Additional Datac0-specific information - these are not referenced anywhere else.
        # self.sig0_datac0_payload_per_frame = self.sig0_datac0_bytes_per_frame - 2
        # self.sig0_datac0_n_nom_modem_samples = codec2.api.freedv_get_n_nom_modem_samples(
        #     self.sig0_datac0_freedv
        # )
        # self.sig0_datac0_n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(
        #     self.sig0_datac0_freedv
        # )
        # self.sig0_datac0_n_tx_preamble_modem_samples = (
        #     codec2.api.freedv_get_n_tx_preamble_modem_samples(self.sig0_datac0_freedv)
        # )
        # self.sig0_datac0_n_tx_postamble_modem_samples = (
        #     codec2.api.freedv_get_n_tx_postamble_modem_samples(self.sig0_datac0_freedv)
        # )

        # return values
        return c2instance, bytes_per_frame, bytes_out, audio_buffer, nin

    def audio_sig0_datac13(self) -> None:
        """Receive data encoded with datac13 - 0"""
        self.sig0_datac13_nin = self.demodulate_audio(
            self.sig0_datac13_buffer,
            self.sig0_datac13_nin,
            self.sig0_datac13_freedv,
            self.sig0_datac13_bytes_out,
            self.sig0_datac13_bytes_per_frame,
            SIG0_DATAC13_STATE,
            "sig0-datac13"
        )

    def audio_sig1_datac13(self) -> None:
        """Receive data encoded with datac13 - 1"""
        self.sig1_datac13_nin = self.demodulate_audio(
            self.sig1_datac13_buffer,
            self.sig1_datac13_nin,
            self.sig1_datac13_freedv,
            self.sig1_datac13_bytes_out,
            self.sig1_datac13_bytes_per_frame,
            SIG1_DATAC13_STATE,
            "sig1-datac13"
        )

    def audio_dat0_datac4(self) -> None:
        """Receive data encoded with datac4"""
        self.dat0_datac4_nin = self.demodulate_audio(
            self.dat0_datac4_buffer,
            self.dat0_datac4_nin,
            self.dat0_datac4_freedv,
            self.dat0_datac4_bytes_out,
            self.dat0_datac4_bytes_per_frame,
            DAT0_DATAC4_STATE,
            "dat0-datac4"
        )

    def audio_dat0_datac1(self) -> None:
        """Receive data encoded with datac1"""
        self.dat0_datac1_nin = self.demodulate_audio(
            self.dat0_datac1_buffer,
            self.dat0_datac1_nin,
            self.dat0_datac1_freedv,
            self.dat0_datac1_bytes_out,
            self.dat0_datac1_bytes_per_frame,
            DAT0_DATAC1_STATE,
            "dat0-datac1"
        )

    def audio_dat0_datac3(self) -> None:
        """Receive data encoded with datac3"""
        self.dat0_datac3_nin = self.demodulate_audio(
            self.dat0_datac3_buffer,
            self.dat0_datac3_nin,
            self.dat0_datac3_freedv,
            self.dat0_datac3_bytes_out,
            self.dat0_datac3_bytes_per_frame,
            DAT0_DATAC3_STATE,
            "dat0-datac3"
        )

    def audio_fsk_ldpc_0(self) -> None:
        """Receive data encoded with FSK + LDPC0"""
        self.fsk_ldpc_nin_0 = self.demodulate_audio(
            self.fsk_ldpc_buffer_0,
            self.fsk_ldpc_nin_0,
            self.fsk_ldpc_freedv_0,
            self.fsk_ldpc_bytes_out_0,
            self.fsk_ldpc_bytes_per_frame_0,
            FSK_LDPC0_STATE,
            "fsk_ldpc0",
        )

    def audio_fsk_ldpc_1(self) -> None:
        """Receive data encoded with FSK + LDPC1"""
        self.fsk_ldpc_nin_1 = self.demodulate_audio(
            self.fsk_ldpc_buffer_1,
            self.fsk_ldpc_nin_1,
            self.fsk_ldpc_freedv_1,
            self.fsk_ldpc_bytes_out_1,
            self.fsk_ldpc_bytes_per_frame_1,
            FSK_LDPC1_STATE,
            "fsk_ldpc1",
        )

    def init_data_threads(self):
        # self.log.debug("[MDM] Starting worker_receive")
        worker_received = threading.Thread(
            target=self.worker_received, name="WORKER_THREAD", daemon=True
        )
        worker_received.start()

        worker_transmit = threading.Thread(
            target=self.worker_transmit, name="WORKER_THREAD", daemon=True
        )
        worker_transmit.start()

    def worker_transmit(self) -> None:
        """Worker for FIFO queue for processing frames to be transmitted"""
        while True:
            # print queue size for debugging purposes
            # TODO Lets check why we have several frames in our transmit queue which causes sometimes a double transmission
            # we could do a cleanup after a transmission so theres no reason sending twice
            queuesize = self.modem_transmit_queue.qsize()
            self.log.debug("[MDM] self.modem_transmit_queue", qsize=queuesize)
            tx = self.modem_transmit_queue.get()

            # TODO Why we is this taking an array instead of a single frame?
            if tx['mode'] in ["morse"]:
                self.transmit_morse(tx['repeat'], tx['repeat_delay'], [tx['frame']])
            else:
                self.transmit(tx['mode'], tx['repeat'], tx['repeat_delay'], [tx['frame']])
            # self.modem_transmit_queue.task_done()

    def worker_received(self) -> None:
        """Worker for FIFO queue for processing received frames"""
        while True:
            data = self.modem_received_queue.get()
            self.log.debug("[MDM] worker_received: received data!")
            # data[0] = bytes_out
            # data[1] = freedv session
            # data[2] = bytes_per_frame
            # data[3] = snr
            DATA_QUEUE_RECEIVED.put([data[0], data[1], data[2], data[3]])
            self.modem_received_queue.task_done()

    def get_frequency_offset(self, freedv: ctypes.c_void_p) -> float:
        """
        Ask codec2 for the calculated (audio) frequency offset of the received signal.

        :param freedv: codec2 instance to query
        :type freedv: ctypes.c_void_p
        :return: Offset of audio frequency in Hz
        :rtype: float
        """
        modemStats = codec2.MODEMSTATS()
        codec2.api.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats))
        offset = round(modemStats.foff) * (-1)
        return offset

    def get_scatter(self, freedv: ctypes.c_void_p) -> None:
        """
        Ask codec2 for data about the received signal and calculate the scatter plot.

        :param freedv: codec2 instance to query
        :type freedv: ctypes.c_void_p
        """
       
        modemStats = codec2.MODEMSTATS()
        ctypes.cast(
            codec2.api.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats)),
            ctypes.c_void_p,
        )

        scatterdata = []
        # original function before itertool
        # for i in range(codec2.MODEM_STATS_NC_MAX):
        #    for j in range(1, codec2.MODEM_STATS_NR_MAX, 2):
        #        # print(f"{modemStats.rx_symbols[i][j]} - {modemStats.rx_symbols[i][j]}")
        #        xsymbols = round(modemStats.rx_symbols[i][j - 1] // 1000)
        #        ysymbols = round(modemStats.rx_symbols[i][j] // 1000)
        #        if xsymbols != 0.0 and ysymbols != 0.0:
        #            scatterdata.append({"x": str(xsymbols), "y": str(ysymbols)})

        for i, j in itertools.product(range(codec2.MODEM_STATS_NC_MAX), range(1, codec2.MODEM_STATS_NR_MAX, 2)):
            # print(f"{modemStats.rx_symbols[i][j]} - {modemStats.rx_symbols[i][j]}")
            xsymbols = round(modemStats.rx_symbols[i][j - 1] // 1000)
            ysymbols = round(modemStats.rx_symbols[i][j] // 1000)
            if xsymbols != 0.0 and ysymbols != 0.0:
                scatterdata.append({"x": str(xsymbols), "y": str(ysymbols)})

        # Send all the data if we have too-few samples, otherwise send a sampling
        if 150 > len(scatterdata) > 0:
            self.event_manager.send_scatter_change(scatterdata)

        else:
            # only take every tenth data point
            self.event_manager.send_scatter_change(scatterdata[::10])

    def calculate_snr(self, freedv: ctypes.c_void_p) -> float:
        """
        Ask codec2 for data about the received signal and calculate
        the signal-to-noise ratio.

        :param freedv: codec2 instance to query
        :type freedv: ctypes.c_void_p
        :return: Signal-to-noise ratio of the decoded data
        :rtype: float
        """
        try:
            modem_stats_snr = ctypes.c_float()
            modem_stats_sync = ctypes.c_int()

            codec2.api.freedv_get_modem_stats(
                freedv, ctypes.byref(modem_stats_sync), ctypes.byref(modem_stats_snr)
            )
            modem_stats_snr = modem_stats_snr.value
            modem_stats_sync = modem_stats_sync.value

            snr = round(modem_stats_snr, 1)
            self.log.info("[MDM] calculate_snr: ", snr=snr)
            # snr = np.clip(
            #    snr, -127, 127
            # )  # limit to max value of -128/128 as a possible fix of #188
            return snr
        except Exception as err:
            self.log.error(f"[MDM] calculate_snr: Exception: {err}")
            return 0

    def init_rig_control(self):
        # Check how we want to control the radio
        if self.radiocontrol == "rigctld":
            import rigctld as rig
        elif self.radiocontrol == "tci":
            self.radio = self.tci_module
        else:
            import rigdummy as rig

        if not self.radiocontrol in ["tci"]:
            self.radio = rig.radio()
            self.radio.open_rig(
                rigctld_ip=self.rigctld_ip,
                rigctld_port=self.rigctld_port,
            )
            hamlib_thread = threading.Thread(
                target=self.update_rig_data, name="HAMLIB_THREAD", daemon=True
            )
        hamlib_thread.start()

        hamlib_set_thread = threading.Thread(
            target=self.set_rig_data, name="HAMLIB_SET_THREAD", daemon=True
        )
        hamlib_set_thread.start()

    def set_rig_data(self) -> None:
        """
            Set rigctld parameters like frequency, mode
            THis needs to be processed in a queue
        """
        while True:
            cmd = RIGCTLD_COMMAND_QUEUE.get()
            if cmd[0] == "set_frequency":
                # [1] = Frequency
                self.radio.set_frequency(cmd[1])
            if cmd[0] == "set_mode":
                # [1] = Mode
                self.radio.set_mode(cmd[1])

    def update_rig_data(self) -> None:
        """
        Request information about the current state of the radio via hamlib
        """
        while True:
            try:
                # this looks weird, but is necessary for avoiding rigctld packet colission sock
                #threading.Event().wait(0.1)
                self.states.set("radio_status", self.radio.get_status())
                #threading.Event().wait(0.25)
                self.states.set("radio_frequency", self.radio.get_frequency())
                threading.Event().wait(0.1)
                self.states.set("radio_mode", self.radio.get_mode())
                threading.Event().wait(0.1)
                self.states.set("radio_bandwidth", self.radio.get_bandwidth())
                threading.Event().wait(0.1)
                if self.states.isTransmitting():
                    self.radio_alc = self.radio.get_alc()
                    threading.Event().wait(0.1)
                self.states.set("radio_rf_power", self.radio.get_level())
                threading.Event().wait(0.1)
                self.states.set("radio_strength", self.radio.get_strength())

            except Exception as e:
                self.log.warning(
                    "[MDM] error getting radio data",
                    e=e,
                )
                threading.Event().wait(1)

    def calculate_fft(self, data) -> None:
        """
        Calculate an average signal strength of the channel to assess
        whether the channel is "busy."
        """
        # Initialize dbfs counter
        rms_counter = 0

        # https://gist.github.com/ZWMiller/53232427efc5088007cab6feee7c6e4c
        # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
        # and make sure it's not imaginary
        try:
            fftarray = np.fft.rfft(data)

            # Set value 0 to 1 to avoid division by zero
            fftarray[fftarray == 0] = 1
            dfft = 10.0 * np.log10(abs(fftarray))

            # get average of dfft
            avg = np.mean(dfft)

            # Detect signals which are higher than the
            # average + 10 (+10 smoothes the output).
            # Data higher than the average must be a signal.
            # Therefore we are setting it to 100 so it will be highlighted
            # Have to do this when we are not transmitting so our
            # own sending data will not affect this too much
            if not self.states.isTransmitting():
                dfft[dfft > avg + 15] = 100

                # Calculate audio dbfs
                # https://stackoverflow.com/a/9763652
                # calculate dbfs every 50 cycles for reducing CPU load
                rms_counter += 1
                if rms_counter > 50:
                    d = np.frombuffer(data, np.int16).astype(np.float32)
                    # calculate RMS and then dBFS
                    # https://dsp.stackexchange.com/questions/8785/how-to-compute-dbfs
                    # try except for avoiding runtime errors by division/0
                    try:
                        rms = int(np.sqrt(np.max(d ** 2)))
                        if rms == 0:
                            raise ZeroDivisionError
                        audio_dbfs = 20 * np.log10(rms / 32768)
                        self.states.set("audio_dbfs", audio_dbfs)
                    except Exception as e:
                        self.states.set("audio_dbfs", -100)


                    rms_counter = 0

            # Convert data to int to decrease size
            dfft = dfft.astype(int)

            # Create list of dfft
            dfftlist = dfft.tolist()

            # Reduce area where the busy detection is enabled
            # We want to have this in correlation with mode bandwidth
            # TODO This is not correctly and needs to be checked for correct maths
            # dfftlist[0:1] = 10,15Hz
            # Bandwidth[Hz] / 10,15
            # narrowband = 563Hz = 56
            # wideband = 1700Hz = 167
            # 1500Hz = 148
            # 2700Hz = 266
            # 3200Hz = 315

            # slot
            slot = 0
            slot1 = [0, 65]
            slot2 = [65,120]
            slot3 = [120, 176]
            slot4 = [176, 231]
            slot5 = [231, len(dfftlist)]
            slotbusy = [False,False,False,False,False]

            # Set to true if we should increment delay count; else false to decrement
            addDelay=False
            for range in [slot1, slot2, slot3, slot4, slot5]:

                range_start = range[0]
                range_end = range[1]
                # define the area, we are detecting busy state
                slotdfft = dfft[range_start:range_end]
                # Check for signals higher than average by checking for "100"
                # If we have a signal, increment our channel_busy delay counter
                # so we have a smoother state toggle
                if np.sum(slotdfft[slotdfft > avg + 15]) >= 200 and not self.states.isTransmitting():
                    addDelay=True
                    slotbusy[slot]=True
                    #self.states.channel_busy_slot[slot] = True
                # increment slot
                slot += 1
                self.states.set_channel_slot_busy(slotbusy)
            if addDelay:
                # Limit delay counter to a maximum of 200. The higher this value,
                # the longer we will wait until releasing state
                self.states.set("channel_busy", True)
                self.channel_busy_delay = min(self.channel_busy_delay + 10, 200)
            else:
                # Decrement channel busy counter if no signal has been detected.
                self.channel_busy_delay = max(self.channel_busy_delay - 1, 0)
                # When our channel busy counter reaches 0, toggle state to False
                if self.channel_busy_delay == 0:
                    self.states.set("channel_busy", False)
            if (self.enable_fft_stream):
                # erase queue if greater than 10
                if self.fft_queue.qsize() >= 10:
                    self.fft_queue = queue.Queue()
                self.fft_queue.put(dfftlist[:315]) # 315 --> bandwidth 3200
        except Exception as err:
            self.log.error(f"[MDM] calculate_fft: Exception: {err}")
            self.log.debug("[MDM] Setting fft=0")
            # else 0
            self.fft_queue.put([0])

    def set_frames_per_burst(self, frames_per_burst: int) -> None:
        """
        Configure codec2 to send the configured number of frames per burst.

        :param frames_per_burst: Number of frames per burst requested
        :type frames_per_burst: int
        """
        # Limit frames per burst to acceptable values
        frames_per_burst = min(frames_per_burst, 1)
        frames_per_burst = max(frames_per_burst, 5)

        frames_per_burst = 1

        codec2.api.freedv_set_frames_per_burst(self.dat0_datac1_freedv, frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.dat0_datac3_freedv, frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.dat0_datac4_freedv, frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.fsk_ldpc_freedv_0, frames_per_burst)

    def reset_data_sync(self) -> None:
        """
        reset sync state for data modes

        :param frames_per_burst: Number of frames per burst requested
        :type frames_per_burst: int
        """

        codec2.api.freedv_set_sync(self.dat0_datac1_freedv, 0)
        codec2.api.freedv_set_sync(self.dat0_datac3_freedv, 0)
        codec2.api.freedv_set_sync(self.dat0_datac4_freedv, 0)
        codec2.api.freedv_set_sync(self.fsk_ldpc_freedv_0, 0)

    def set_FFT_stream(self, enable: bool):
        # Set config boolean regarding wheter it should sent FFT data to queue
        self.enable_fft_stream = enable

def set_audio_volume(datalist: np.ndarray, dB: float) -> np.ndarray:
    """
    Scale values for the provided audio samples by dB.

    :param datalist: Audio samples to scale
    :type datalist: np.ndarray
    :param dB: Decibels to scale samples, constrained to the range [-50, 50]
    :type dB: float
    :return: Scaled audio samples
    :rtype: np.ndarray
    """
    try:
        dB = float(dB)
    except ValueError as e:
        print(f"[MDM] Changing audio volume failed with error: {e}")
        dB = 0.0  # 0 dB means no change

    # Clip dB value to the range [-50, 50]
    dB = np.clip(dB, -30, 20)

    # Ensure datalist is an np.ndarray
    if not isinstance(datalist, np.ndarray):
        print("[MDM] Invalid data type for datalist. Expected np.ndarray.")
        return datalist

    # Convert dB to linear scale
    scale_factor = 10 ** (dB / 20)

    # Scale samples
    scaled_data = datalist * scale_factor

    # Clip values to int16 range and convert data type
    return np.clip(scaled_data, -32768, 32767).astype(np.int16)

def get_modem_error_state():
    """
    get current state buffer and return True of contains 10

    """

    if RECEIVE_DATAC1 and 10 in DAT0_DATAC1_STATE:
        DAT0_DATAC1_STATE.clear()
        return True
    if RECEIVE_DATAC3 and 10 in DAT0_DATAC3_STATE:
        DAT0_DATAC3_STATE.clear()
        return True
    if RECEIVE_DATAC4 and 10 in DAT0_DATAC4_STATE:
        DAT0_DATAC4_STATE.clear()
        return True

    return False
