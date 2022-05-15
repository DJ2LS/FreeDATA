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
import logging
import os
import pathlib
import queue
import re
import sys
import threading
import time
from collections import deque

import numpy as np
import sounddevice as sd
import structlog
import ujson as json

import audio
import codec2
import data_handler
import helpers
import log_handler
import sock
import static

TESTMODE = False
RXCHANNEL = ''
TXCHANNEL = ''

# Initialize FIFO queue to store received frames
MODEM_RECEIVED_QUEUE = queue.Queue()
MODEM_TRANSMIT_QUEUE = queue.Queue()
static.TRANSMITTING = False

# Receive only specific modes to reduce CPU load
RECEIVE_DATAC1 = False
RECEIVE_DATAC3 = False
RECEIVE_FSK_LDPC_1 = False

class RF():
    """ """
    def __init__(self):

        self.sampler_avg = 0
        self.buffer_avg = 0

        self.AUDIO_SAMPLE_RATE_RX = 48000
        self.AUDIO_SAMPLE_RATE_TX = 48000
        self.MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
        self.AUDIO_FRAMES_PER_BUFFER_RX = 2400 * 2  # 8192
        self.AUDIO_FRAMES_PER_BUFFER_TX = 2400 * 2  # 8192 Lets to some tests with very small chunks for TX
        self.AUDIO_CHUNKS = 48  # 8 * (self.AUDIO_SAMPLE_RATE_RX/self.MODEM_SAMPLE_RATE) #48
        self.AUDIO_CHANNELS = 1

        # Locking state for mod out so buffer will be filled before we can use it
        # https://github.com/DJ2LS/FreeDATA/issues/127
        # https://github.com/DJ2LS/FreeDATA/issues/99
        self.mod_out_locked = True

        # Make sure our resampler will work
        assert (self.AUDIO_SAMPLE_RATE_RX / self.MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48

        # Small hack for initializing codec2 via codec2.py module
        # TODO: Need to change the entire modem module to integrate codec2 module
        self.c_lib = codec2.api
        self.resampler = codec2.resampler()

        self.modem_transmit_queue = MODEM_TRANSMIT_QUEUE
        self.modem_received_queue = MODEM_RECEIVED_QUEUE

        # Init FIFO queue to store modulation out in
        self.modoutqueue = deque()

        # Define fft_data buffer
        self.fft_data = bytes()

        # Open codec2 instances
        self.datac0_freedv = ctypes.cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC0), ctypes.c_void_p)
        self.c_lib.freedv_set_tuning_range(self.datac0_freedv, ctypes.c_float(static.TUNING_RANGE_FMIN), ctypes.c_float(static.TUNING_RANGE_FMAX))
        self.datac0_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac0_freedv) / 8)
        self.datac0_payload_per_frame = self.datac0_bytes_per_frame - 2
        self.datac0_n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(self.datac0_freedv)
        self.datac0_n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(self.datac0_freedv)
        self.datac0_n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(self.datac0_freedv)
        self.datac0_n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(self.datac0_freedv)
        self.datac0_bytes_out = ctypes.create_string_buffer(self.datac0_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac0_freedv, 1)
        self.datac0_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER_RX)

        self.datac1_freedv = ctypes.cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC1), ctypes.c_void_p)
        self.c_lib.freedv_set_tuning_range(self.datac1_freedv, ctypes.c_float(static.TUNING_RANGE_FMIN), ctypes.c_float(static.TUNING_RANGE_FMAX))
        self.datac1_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac1_freedv) / 8)
        self.datac1_bytes_out = ctypes.create_string_buffer(self.datac1_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac1_freedv, 1)
        self.datac1_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER_RX)

        self.datac3_freedv = ctypes.cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC3), ctypes.c_void_p)
        self.c_lib.freedv_set_tuning_range(self.datac3_freedv, ctypes.c_float(static.TUNING_RANGE_FMIN), ctypes.c_float(static.TUNING_RANGE_FMAX))
        self.datac3_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac3_freedv) / 8)
        self.datac3_bytes_out = ctypes.create_string_buffer(self.datac3_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac3_freedv, 1)
        self.datac3_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER_RX)

        self.fsk_ldpc_freedv_0 = ctypes.cast(codec2.api.freedv_open_advanced(codec2.api.FREEDV_MODE_FSK_LDPC, ctypes.byref(codec2.api.FREEDV_MODE_FSK_LDPC_0_ADV)), ctypes.c_void_p)
        self.fsk_ldpc_bytes_per_frame_0 = int(codec2.api.freedv_get_bits_per_modem_frame(self.fsk_ldpc_freedv_0) / 8)
        self.fsk_ldpc_bytes_out_0 = ctypes.create_string_buffer(self.fsk_ldpc_bytes_per_frame_0)
        #codec2.api.freedv_set_frames_per_burst(self.fsk_ldpc_freedv_0, 1)
        self.fsk_ldpc_buffer_0 = codec2.audio_buffer(self.AUDIO_FRAMES_PER_BUFFER_RX)

        self.fsk_ldpc_freedv_1 = ctypes.cast(codec2.api.freedv_open_advanced(codec2.api.FREEDV_MODE_FSK_LDPC, ctypes.byref(codec2.api.FREEDV_MODE_FSK_LDPC_1_ADV)), ctypes.c_void_p)
        self.fsk_ldpc_bytes_per_frame_1 = int(codec2.api.freedv_get_bits_per_modem_frame(self.fsk_ldpc_freedv_1) / 8)
        self.fsk_ldpc_bytes_out_1 = ctypes.create_string_buffer(self.fsk_ldpc_bytes_per_frame_1)
        #codec2.api.freedv_set_frames_per_burst(self.fsk_ldpc_freedv_0, 1)
        self.fsk_ldpc_buffer_1 = codec2.audio_buffer(self.AUDIO_FRAMES_PER_BUFFER_RX)

        # initial nin values
        self.datac0_nin = codec2.api.freedv_nin(self.datac0_freedv)
        self.datac1_nin = codec2.api.freedv_nin(self.datac1_freedv)
        self.datac3_nin = codec2.api.freedv_nin(self.datac3_freedv)
        self.fsk_ldpc_nin_0 = codec2.api.freedv_nin(self.fsk_ldpc_freedv_0)
        self.fsk_ldpc_nin_1 = codec2.api.freedv_nin(self.fsk_ldpc_freedv_1)
        # --------------------------------------------CREATE PYAUDIO INSTANCE
        if not TESTMODE:
            try:
                self.stream = sd.RawStream(channels=1, dtype='int16', callback=self.callback, device=(static.AUDIO_INPUT_DEVICE, static.AUDIO_OUTPUT_DEVICE), samplerate = self.AUDIO_SAMPLE_RATE_RX, blocksize=4800)
                atexit.register(self.stream.stop)
                structlog.get_logger("structlog").info("[MDM] init: opened audio devices")

            except Exception as e:
                structlog.get_logger("structlog").error("[MDM] init: can't open audio device. Exit", e=e)
                sys.exit(1)

            try:
                structlog.get_logger("structlog").debug("[MDM] init: starting pyaudio callback")
                #self.audio_stream.start_stream()
                self.stream.start()

            except Exception as e:
                structlog.get_logger("structlog").error("[MDM] init: starting pyaudio callback failed", e=e)

        else:
            # create a stream object for simulating audio stream
            class Object(object):
                pass
            self.stream = Object()
            self.stream.active = True

            # create mkfifo buffer
            try:
                os.mkfifo(RXCHANNEL)
                os.mkfifo(TXCHANNEL)
            except Exception as e:
                structlog.get_logger("structlog").error(f"[MDM] init:mkfifo: Exception: {e}")
                pass

            mkfifo_write_callback_thread = threading.Thread(target=self.mkfifo_write_callback, name="MKFIFO WRITE CALLBACK THREAD",daemon=True)
            mkfifo_write_callback_thread.start()

            mkfifo_read_callback_thread = threading.Thread(target=self.mkfifo_read_callback, name="MKFIFO READ CALLBACK THREAD",daemon=True)
            mkfifo_read_callback_thread.start()

        # --------------------------------------------INIT AND OPEN HAMLIB
        # Check how we want to control the radio
        if static.HAMLIB_RADIOCONTROL == 'direct':
            import rig
        elif static.HAMLIB_RADIOCONTROL == 'rigctl':
            import rigctl as rig
        elif static.HAMLIB_RADIOCONTROL == 'rigctld':
            import rigctld as rig
        elif static.HAMLIB_RADIOCONTROL == 'disabled':
            import rigdummy as rig
        else:
            import rigdummy as rig

        self.hamlib = rig.radio()
        self.hamlib.open_rig(devicename=static.HAMLIB_DEVICE_NAME, deviceport=static.HAMLIB_DEVICE_PORT, hamlib_ptt_type=static.HAMLIB_PTT_TYPE, serialspeed=static.HAMLIB_SERIAL_SPEED, pttport=static.HAMLIB_PTT_PORT, data_bits=static.HAMLIB_DATA_BITS, stop_bits=static.HAMLIB_STOP_BITS, handshake=static.HAMLIB_HANDSHAKE, rigctld_ip = static.HAMLIB_RIGCTLD_IP, rigctld_port = static.HAMLIB_RIGCTLD_PORT)

        # --------------------------------------------START DECODER THREAD
        if static.ENABLE_FFT:
            fft_thread = threading.Thread(target=self.calculate_fft, name="FFT_THREAD", daemon=True)
            fft_thread.start()

        audio_thread_datac0 = threading.Thread(target=self.audio_datac0, name="AUDIO_THREAD DATAC0", daemon=True)
        audio_thread_datac0.start()

        audio_thread_datac1 = threading.Thread(target=self.audio_datac1, name="AUDIO_THREAD DATAC1", daemon=True)
        audio_thread_datac1.start()

        audio_thread_datac3 = threading.Thread(target=self.audio_datac3, name="AUDIO_THREAD DATAC3", daemon=True)
        audio_thread_datac3.start()

        if static.ENABLE_FSK:
            audio_thread_fsk_ldpc0 = threading.Thread(target=self.audio_fsk_ldpc_0, name="AUDIO_THREAD FSK LDPC0", daemon=True)
            audio_thread_fsk_ldpc0.start()

            audio_thread_fsk_ldpc1 = threading.Thread(target=self.audio_fsk_ldpc_1, name="AUDIO_THREAD FSK LDPC1", daemon=True)
            audio_thread_fsk_ldpc1.start()

        hamlib_thread = threading.Thread(target=self.update_rig_data, name="HAMLIB_THREAD", daemon=True)
        hamlib_thread.start()

        worker_received = threading.Thread(target=self.worker_received, name="WORKER_THREAD", daemon=True)
        worker_received.start()

        worker_transmit = threading.Thread(target=self.worker_transmit, name="WORKER_THREAD", daemon=True)
        worker_transmit.start()

    # --------------------------------------------------------------------------------------------------------
    def mkfifo_read_callback(self):
        while 1:
            time.sleep(0.01)
            # -----read
            data_in48k = bytes()
            with open(RXCHANNEL, 'rb') as fifo:
                for line in fifo:
                    data_in48k += line

                    while len(data_in48k) >= 48:
                        x = np.frombuffer(data_in48k[:48], dtype=np.int16)
                        x = self.resampler.resample48_to_8(x)
                        data_in48k = data_in48k[48:]

                        length_x = len(x)
                        if not self.datac0_buffer.nbuffer + length_x > self.datac0_buffer.size:
                            self.datac0_buffer.push(x)

                        if not self.datac1_buffer.nbuffer + length_x > self.datac1_buffer.size and RECEIVE_DATAC1:
                                self.datac1_buffer.push(x)

                        if not self.datac3_buffer.nbuffer + length_x > self.datac3_buffer.size and RECEIVE_DATAC3:
                                self.datac3_buffer.push(x)

    def mkfifo_write_callback(self):
        while 1:
            time.sleep(0.01)

            # -----write
            if len(self.modoutqueue) <= 0 or self.mod_out_locked:
                #data_out48k = np.zeros(self.AUDIO_FRAMES_PER_BUFFER_RX, dtype=np.int16)
                pass

            else:
                data_out48k = self.modoutqueue.popleft()
                #print(len(data_out48k))

                fifo_write = open(TXCHANNEL, 'wb')
                fifo_write.write(data_out48k)
                fifo_write.flush()

    # --------------------------------------------------------------------
    def callback(self, data_in48k, outdata, frames, time, status):
        """

        Args:
            data_in48k: Incoming data received
            outdata: Container for the data returned
            frames: Number of frames
            time:
          status:

        Returns:
            Nothing
        """
        x = np.frombuffer(data_in48k, dtype=np.int16)
        x = self.resampler.resample48_to_8(x)

        # Avoid decoding when transmitting to reduce CPU
        if not static.TRANSMITTING:
            length_x = len(x)
            # Avoid buffer overflow by filling only if buffer not full
            if not self.datac0_buffer.nbuffer + length_x > self.datac0_buffer.size:
                self.datac0_buffer.push(x)
            else:
                static.BUFFER_OVERFLOW_COUNTER[0] += 1

            # Avoid buffer overflow by filling only if buffer not full and selected datachannel mode
            if not self.datac1_buffer.nbuffer + length_x > self.datac1_buffer.size:
                if RECEIVE_DATAC1:
                    self.datac1_buffer.push(x)
            else:
                static.BUFFER_OVERFLOW_COUNTER[1] += 1

            # Avoid buffer overflow by filling only if buffer not full and selected datachannel mode
            if not self.datac3_buffer.nbuffer + length_x > self.datac3_buffer.size:
                if RECEIVE_DATAC3:
                    self.datac3_buffer.push(x)
            else:
                static.BUFFER_OVERFLOW_COUNTER[2] += 1

            # Avoid buffer overflow by filling only if buffer not full and selected datachannel mode
            if not self.fsk_ldpc_buffer_0.nbuffer + length_x > self.fsk_ldpc_buffer_0.size:
                if static.ENABLE_FSK:
                    self.fsk_ldpc_buffer_0.push(x)
            else:
                static.BUFFER_OVERFLOW_COUNTER[3] += 1

            # Avoid buffer overflow by filling only if buffer not full and selected datachannel mode
            if not self.fsk_ldpc_buffer_1.nbuffer + length_x > self.fsk_ldpc_buffer_1.size:
                if RECEIVE_FSK_LDPC_1 and static.ENABLE_FSK:
                    self.fsk_ldpc_buffer_1.push(x)
            else:
                static.BUFFER_OVERFLOW_COUNTER[4] += 1

        if len(self.modoutqueue) <= 0 or self.mod_out_locked:
        # if not self.modoutqueue or self.mod_out_locked:
            data_out48k = np.zeros(frames, dtype=np.int16)
            self.fft_data = x
        else:
            data_out48k = self.modoutqueue.popleft()
            self.fft_data = data_out48k

        try:
            outdata[:] = data_out48k[:frames]
        except IndexError as e:
            structlog.get_logger("structlog").debug(f"[MDM] callback: IndexError: {e}")

        # return (data_out48k, audio.pyaudio.paContinue)

    # --------------------------------------------------------------------
    def transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray):
        """

        Args:
          mode:
          repeats:
          repeat_delay:
          frames:

        Returns:

        """
        structlog.get_logger("structlog").debug("[MDM] transmit", mode=mode)
        static.TRANSMITTING = True
        # Toggle ptt early to save some time and send ptt state via socket
        static.PTT_STATE = self.hamlib.set_ptt(True)
        jsondata = {"ptt":"True"}
        data_out = json.dumps(jsondata)
        sock.SOCKET_QUEUE.put(data_out)

        # Open codec2 instance
        self.MODE = mode
        freedv = open_codec2_instance(self.MODE)

        # Get number of bytes per frame for mode
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_bytes_per_frame = bytes_per_frame - 2

        # Init buffer for data
        n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
        mod_out = ctypes.create_string_buffer(n_tx_modem_samples * 2)

        # Init buffer for preample
        n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(freedv)
        mod_out_preamble = ctypes.create_string_buffer(n_tx_preamble_modem_samples * 2)

        # Init buffer for postamble
        n_tx_postamble_modem_samples = codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
        mod_out_postamble = ctypes.create_string_buffer(n_tx_postamble_modem_samples * 2)

        # Add empty data to handle ptt toggle time
        data_delay_mseconds = 0  # milliseconds
        data_delay = int(self.MODEM_SAMPLE_RATE * (data_delay_mseconds / 1000))
        mod_out_silence = ctypes.create_string_buffer(data_delay * 2)
        txbuffer = bytes(mod_out_silence)

        structlog.get_logger("structlog").debug("[MDM] TRANSMIT", mode=self.MODE, payload=payload_bytes_per_frame)

        for _ in range(repeats):
            # codec2 fsk preamble may be broken - at least it sounds like that so we are disabling it for testing
            if self.MODE not in ['FSK_LDPC_0', 'FSK_LDPC_1', 200, 201]:
                # Write preamble to txbuffer
                codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
                txbuffer += bytes(mod_out_preamble)

            # Create modulaton for n frames in list
            for n in range(len(frames)):
                # Create buffer for data
                buffer = bytearray(payload_bytes_per_frame)  # Use this if CRC16 checksum is required ( DATA1-3)
                buffer[:len(frames[n])] = frames[n]  # Set buffersize to length of data which will be send

                # Create crc for data frame - we are using the crc function shipped with codec2 to avoid
                # CRC algorithm incompatibilities
                crc = ctypes.c_ushort(codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame))  # Generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big')  # Convert crc to 2 byte hex string
                buffer += crc  # Append crc16 to buffer

                data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
                codec2.api.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and save it into mod_out pointer
                txbuffer += bytes(mod_out)

            # codec2 fsk postamble may be broken - at least it sounds like that so we are disabling it for testing
            if self.MODE not in ['FSK_LDPC_0', 'FSK_LDPC_1', 200, 201]:
                # Write postamble to txbuffer
                codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
                # Append postamble to txbuffer
                txbuffer += bytes(mod_out_postamble)

            # Add delay to end of frames
            samples_delay = int(self.MODEM_SAMPLE_RATE * (repeat_delay / 1000))
            mod_out_silence = ctypes.create_string_buffer(samples_delay * 2)
            txbuffer += bytes(mod_out_silence)

        # Re-sample back up to 48k (resampler works on np.int16)
        x = np.frombuffer(txbuffer, dtype=np.int16)
        x = set_audio_volume(x, static.TX_AUDIO_LEVEL)

        txbuffer_48k = self.resampler.resample8_to_48(x)

        # Explicitly lock our usage of mod_out_queue if needed
        # Deaktivated for testing purposes
        self.mod_out_locked = False

        # -------------------------------
        chunk_length = self.AUDIO_FRAMES_PER_BUFFER_TX #4800
        chunk = [txbuffer_48k[i:i+chunk_length] for i in range(0, len(txbuffer_48k), chunk_length)]
        for c in chunk:
            if len(c) < chunk_length:
                delta = chunk_length - len(c)
                delta_zeros = np.zeros(delta, dtype=np.int16)
                c = np.append(c, delta_zeros)
                #structlog.get_logger("structlog").debug("[MDM] mod out shorter than audio buffer", delta=delta)

            self.modoutqueue.append(c)

        # Release our mod_out_lock so we can use the queue
        self.mod_out_locked = False

        while self.modoutqueue:
            time.sleep(0.01)

        static.PTT_STATE = self.hamlib.set_ptt(False)

        # Push ptt state to socket stream
        jsondata = {"ptt":"False"}
        data_out = json.dumps(jsondata)
        sock.SOCKET_QUEUE.put(data_out)

        # After processing, set the locking state back to true to be prepared for next transmission
        self.mod_out_locked = True

        self.c_lib.freedv_close(freedv)
        self.modem_transmit_queue.task_done()
        static.TRANSMITTING = False
        threading.Event().set()

    def audio_datac0(self):
        """ """
        nbytes_datac0 = 0
        while self.stream.active:
            threading.Event().wait(0.01)
            while self.datac0_buffer.nbuffer >= self.datac0_nin:
                # demodulate audio
                nbytes_datac0 = codec2.api.freedv_rawdatarx(self.datac0_freedv, self.datac0_bytes_out, self.datac0_buffer.buffer.ctypes)
                self.datac0_buffer.pop(self.datac0_nin)
                self.datac0_nin = codec2.api.freedv_nin(self.datac0_freedv)
                if nbytes_datac0 == self.datac0_bytes_per_frame:
                    self.modem_received_queue.put([self.datac0_bytes_out, self.datac0_freedv, self.datac0_bytes_per_frame])
                    #self.get_scatter(self.datac0_freedv)
                    self.calculate_snr(self.datac0_freedv)

    def audio_datac1(self):
        """ """
        nbytes_datac1 = 0
        while self.stream.active:
            threading.Event().wait(0.01)
            while self.datac1_buffer.nbuffer >= self.datac1_nin:
                # demodulate audio
                nbytes_datac1 = codec2.api.freedv_rawdatarx(self.datac1_freedv, self.datac1_bytes_out, self.datac1_buffer.buffer.ctypes)
                self.datac1_buffer.pop(self.datac1_nin)
                self.datac1_nin = codec2.api.freedv_nin(self.datac1_freedv)
                if nbytes_datac1 == self.datac1_bytes_per_frame:
                    self.modem_received_queue.put([self.datac1_bytes_out, self.datac1_freedv, self.datac1_bytes_per_frame])
                    #self.get_scatter(self.datac1_freedv)
                    self.calculate_snr(self.datac1_freedv)

    def audio_datac3(self):
        """ """
        nbytes_datac3 = 0
        while self.stream.active:
            threading.Event().wait(0.01)
            while self.datac3_buffer.nbuffer >= self.datac3_nin:
                # demodulate audio
                nbytes_datac3 = codec2.api.freedv_rawdatarx(self.datac3_freedv, self.datac3_bytes_out, self.datac3_buffer.buffer.ctypes)
                self.datac3_buffer.pop(self.datac3_nin)
                self.datac3_nin = codec2.api.freedv_nin(self.datac3_freedv)
                if nbytes_datac3 == self.datac3_bytes_per_frame:
                    self.modem_received_queue.put([self.datac3_bytes_out, self.datac3_freedv, self.datac3_bytes_per_frame])
                    #self.get_scatter(self.datac3_freedv)
                    self.calculate_snr(self.datac3_freedv)

    def audio_fsk_ldpc_0(self):
        """ """
        nbytes_fsk_ldpc_0 = 0
        while self.stream.active and static.ENABLE_FSK:
            threading.Event().wait(0.01)
            while self.fsk_ldpc_buffer_0.nbuffer >= self.fsk_ldpc_nin_0:
                # demodulate audio
                nbytes_fsk_ldpc_0 = codec2.api.freedv_rawdatarx(self.fsk_ldpc_freedv_0, self.fsk_ldpc_bytes_out_0, self.fsk_ldpc_buffer_0.buffer.ctypes)
                self.fsk_ldpc_buffer_0.pop(self.fsk_ldpc_nin_0)
                self.fsk_ldpc_nin_0 = codec2.api.freedv_nin(self.fsk_ldpc_freedv_0)
                if nbytes_fsk_ldpc_0 == self.fsk_ldpc_bytes_per_frame_0:
                    self.modem_received_queue.put([self.fsk_ldpc_bytes_out_0, self.fsk_ldpc_freedv_0, self.fsk_ldpc_bytes_per_frame_0])
                    #self.get_scatter(self.fsk_ldpc_freedv_0)
                    self.calculate_snr(self.fsk_ldpc_freedv_0)

    def audio_fsk_ldpc_1(self):
        """ """
        nbytes_fsk_ldpc_1 = 0
        while self.stream.active and static.ENABLE_FSK:
            threading.Event().wait(0.01)
            while self.fsk_ldpc_buffer_1.nbuffer >= self.fsk_ldpc_nin_1:
                # demodulate audio
                nbytes_fsk_ldpc_1 = codec2.api.freedv_rawdatarx(self.fsk_ldpc_freedv_1, self.fsk_ldpc_bytes_out_1, self.fsk_ldpc_buffer_1.buffer.ctypes)
                self.fsk_ldpc_buffer_1.pop(self.fsk_ldpc_nin_1)
                self.fsk_ldpc_nin_1 = codec2.api.freedv_nin(self.fsk_ldpc_freedv_1)
                if nbytes_fsk_ldpc_1 == self.fsk_ldpc_bytes_per_frame_1:
                    self.modem_received_queue.put([self.fsk_ldpc_bytes_out_1, self.fsk_ldpc_freedv_1, self.fsk_ldpc_bytes_per_frame_1])
                    #self.get_scatter(self.fsk_ldpc_freedv_1)
                    self.calculate_snr(self.fsk_ldpc_freedv_1)

    # worker for FIFO queue for processing received frames
    def worker_transmit(self):
        """ """
        while True:
            data = self.modem_transmit_queue.get()

            structlog.get_logger("structlog").debug("[MDM] worker_transmit", mode=data[0])
            self.transmit(mode=data[0], repeats=data[1], repeat_delay=data[2], frames=data[3])
            #self.modem_transmit_queue.task_done()

    # worker for FIFO queue for processing received frames
    def worker_received(self):
        """ """
        while True:
            data = self.modem_received_queue.get()
            # data[0] = bytes_out
            # data[1] = freedv session
            # data[2] = bytes_per_frame
            data_handler.DATA_QUEUE_RECEIVED.put([data[0], data[1], data[2]])
            self.modem_received_queue.task_done()

    def get_frequency_offset(self, freedv):
        """

        Args:
          freedv:

        Returns:

        """
        modemStats = codec2.MODEMSTATS()
        self.c_lib.freedv_get_modem_extended_stats.restype = None
        self.c_lib.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats))
        offset = round(modemStats.foff) * (-1)
        static.FREQ_OFFSET = offset
        return offset

    def get_scatter(self, freedv):
        """

        Args:
          freedv:

        Returns:

        """
        if not static.ENABLE_SCATTER:
            return

        modemStats = codec2.MODEMSTATS()
        self.c_lib.freedv_get_modem_extended_stats.restype = None
        self.c_lib.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats))

        scatterdata = []
        scatterdata_small = []
        for i in range(codec2.MODEM_STATS_NC_MAX):
            for j in range(codec2.MODEM_STATS_NR_MAX):
                # check if odd or not to get every 2nd item for x
                if (j % 2) == 0:
                    xsymbols = round(modemStats.rx_symbols[i][j] / 1000)
                    ysymbols = round(modemStats.rx_symbols[i][j + 1] / 1000)
                    # check if value 0.0 or has real data
                    if xsymbols != 0.0 and ysymbols != 0.0:
                        scatterdata.append({"x": xsymbols, "y": ysymbols})

        # only append scatter data if new data arrived
        if 150 > len(scatterdata) > 0:
            static.SCATTER = scatterdata
        else:
            # only take every tenth data point
            scatterdata_small = scatterdata[::10]
            static.SCATTER = scatterdata_small

    def calculate_snr(self, freedv):
        """

        Args:
          freedv:

        Returns:

        """
        try:
            modem_stats_snr = ctypes.c_float()
            modem_stats_sync = ctypes.c_int()

            self.c_lib.freedv_get_modem_stats(freedv, ctypes.byref(modem_stats_sync), ctypes.byref(modem_stats_snr))
            modem_stats_snr = modem_stats_snr.value
            modem_stats_sync = modem_stats_sync.value

            snr = round(modem_stats_snr, 1)
            structlog.get_logger("structlog").info("[MDM] calculate_snr: ", snr=snr)
            # print(snr)
            static.SNR = np.clip(snr, 0, 255)  # limit to max value of 255
            return static.SNR
        except Exception as e:
            structlog.get_logger("structlog").error(f"[MDM] calculate_snr: Exception: {e}")
            static.SNR = 0
            return static.SNR

    def update_rig_data(self):
        """ """
        while True:
            # time.sleep(1.5)
            threading.Event().wait(0.5)
            # (static.HAMLIB_FREQUENCY, static.HAMLIB_MODE, static.HAMLIB_BANDWITH, static.PTT_STATE) = self.hamlib.get_rig_data()
            static.HAMLIB_FREQUENCY = self.hamlib.get_frequency()
            static.HAMLIB_MODE = self.hamlib.get_mode()
            static.HAMLIB_BANDWITH = self.hamlib.get_bandwith()

    def calculate_fft(self):
        """ """
        # channel_busy_delay counter
        channel_busy_delay = 0

        while True:
            #time.sleep(0.01)
            threading.Event().wait(0.01)
            # WE NEED TO OPTIMIZE THIS!

            if len(self.fft_data) >= 128:
                # https://gist.github.com/ZWMiller/53232427efc5088007cab6feee7c6e4c
                # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
                # and make sure it's not imaginary
                try:
                    fftarray = np.fft.rfft(self.fft_data)

                    # set value 0 to 1 to avoid division by zero
                    fftarray[fftarray == 0] = 1
                    dfft = 10.*np.log10(abs(fftarray))

                    # get average of dfft
                    avg = np.mean(dfft)

                    # Detect signals which are higher than the average + 10 ( +10 smoothes the output )
                    # Data higher than the average must be a signal. Therefore we are setting it to 100 so it will be highlighted
                    # Have to do this when we are not transmitting so our own sending data will not affect this too much
                    if not static.TRANSMITTING:
                        dfft[dfft>avg+10] = 100

                        # Calculate audio max value
                        # static.AUDIO_RMS = np.amax(self.fft_data)

                    # Check for signals higher than average by checking for "100"
                    # If we have a signal, increment our channel_busy delay counter so we have a smoother state toggle
                    if np.sum(dfft[dfft > avg + 10]) >= 300 and not static.TRANSMITTING:
                        static.CHANNEL_BUSY = True
                        # Limit delay counter to a maximun of 30. The higher this value, the linger we will wait until releasing state
                        channel_busy_delay = min(channel_busy_delay + 5, 50)
                    else:
                        # Decrement channel busy counter if no signal has been detected.
                        channel_busy_delay = max(channel_busy_delay - 1, 0)
                        # If our channel busy counter reached 0, toggle state to False
                        if channel_busy_delay == 0:
                            static.CHANNEL_BUSY = False

                    # round data to decrease size
                    dfft = np.around(dfft, 0)
                    dfftlist = dfft.tolist()

                    static.FFT = dfftlist[:320] #320 --> bandwidth 3000
                except Exception as e:
                    structlog.get_logger("structlog").error(f"[MDM] calculate_fft: Exception: {e}")
                    structlog.get_logger("structlog").debug("[MDM] Setting fft=0")
                    # else 0
                    static.FFT = [0]

    def set_frames_per_burst(self, n_frames_per_burst):
        """

        Args:
          n_frames_per_burst:

        Returns:

        """
        codec2.api.freedv_set_frames_per_burst(self.datac1_freedv, n_frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.datac3_freedv, n_frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.fsk_ldpc_freedv_0, n_frames_per_burst)

def open_codec2_instance(mode):
    """ Return a codec2 instance """
    if mode in ['FSK_LDPC_0', 200]:
        return ctypes.cast(codec2.api.freedv_open_advanced(codec2.api.FREEDV_MODE_FSK_LDPC,
            ctypes.byref(codec2.api.FREEDV_MODE_FSK_LDPC_0_ADV)), ctypes.c_void_p)

    if mode in ['FSK_LDPC_1', 201]:
        return ctypes.cast(codec2.api.freedv_open_advanced(codec2.api.FREEDV_MODE_FSK_LDPC,
            ctypes.byref(codec2.api.FREEDV_MODE_FSK_LDPC_1_ADV)), ctypes.c_void_p)

    return ctypes.cast(codec2.api.freedv_open(mode), ctypes.c_void_p)


def get_bytes_per_frame(mode):
    """
    provide bytes per frame information for accessing from data handler

    Args:
      mode:

    Returns:

    """
    freedv = open_codec2_instance(mode)

    # get number of bytes per frame for mode
    return int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)


def set_audio_volume(datalist, volume):
    data = np.fromstring(datalist, np.int16) * (volume / 100.)
    return data.astype(np.int16)
