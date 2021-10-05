#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""
import sys
import ctypes
from ctypes import *
import pathlib
import audioop
#import asyncio
import logging
import time
import threading
import atexit
import numpy as np
import pyaudio
import helpers
import static
import data_handler



# sys.path.append("hamlib/linux")
try:
    import Hamlib
    print("running Hamlib from Sys Path")
except ImportError:
    from hamlib.linux import Hamlib
    print("running Hamlib from precompiled bundle")
else:
    # place for rigctld
    pass


#import rigctld
#rigctld = rigctld.Rigctld()


MODEM_STATS_NR_MAX = 320
MODEM_STATS_NC_MAX = 51


class MODEMSTATS(ctypes.Structure):
    _fields_ = [
        ("Nc", ctypes.c_int),
        ("snr_est", ctypes.c_float),
        ("rx_symbols", (ctypes.c_float * MODEM_STATS_NR_MAX)*MODEM_STATS_NC_MAX),
        ("nr", ctypes.c_int),
        ("sync", ctypes.c_int),
        ("foff", ctypes.c_float),
        ("rx_timing", ctypes.c_float),
        ("clock_offset", ctypes.c_float),
        ("sync_metric", ctypes.c_float),
        ("pre", ctypes.c_int),
        ("post", ctypes.c_int),
        ("uw_fails", ctypes.c_int),
    ]


class RF():

    def __init__(self):
        self.AUDIO_SAMPLE_RATE_RX = 48000
        self.AUDIO_SAMPLE_RATE_TX = 48000
        self.MODEM_SAMPLE_RATE = 8000
        self.AUDIO_FRAMES_PER_BUFFER = 8192
        self.AUDIO_CHUNKS = 48 #8 * (self.AUDIO_SAMPLE_RATE_RX/self.MODEM_SAMPLE_RATE) #48
        self.AUDIO_CHANNELS = 1
        
        
        # -------------------------------------------- LOAD FREEDV
        try:
            # we check at first for libcodec2 in root - necessary if we want to run it inside a pyinstaller binary
            libname = pathlib.Path("libcodec2.so.1.0")
            self.c_lib = ctypes.CDLL(libname)
            print("running libcodec from INTERNAL library")
        except:
            # if we cant load libcodec from root, we check for subdirectory
            # this is, if we want to run it without beeing build in a dev environment
            libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so.1.0"
            self.c_lib = ctypes.CDLL(libname)
            print("running libcodec from EXTERNAL library")
        # --------------------------------------------CREATE PYAUDIO  INSTANCE
        self.p = pyaudio.PyAudio()
        atexit.register(self.p.terminate)
        # --------------------------------------------OPEN AUDIO CHANNEL RX
        self.stream_rx = self.p.open(format=pyaudio.paInt16,
                                     channels=self.AUDIO_CHANNELS,
                                     rate=self.AUDIO_SAMPLE_RATE_RX,
                                     frames_per_buffer=self.AUDIO_FRAMES_PER_BUFFER,
                                     input=True,
                                     input_device_index=static.AUDIO_INPUT_DEVICE
                                     )
        # --------------------------------------------OPEN AUDIO CHANNEL TX
        self.stream_tx = self.p.open(format=pyaudio.paInt16,
                                     channels=1,
                                     rate=self.AUDIO_SAMPLE_RATE_TX,
                                     frames_per_buffer=self.AUDIO_FRAMES_PER_BUFFER,  # n_nom_modem_samples
                                     output=True,
                                     output_device_index=static.AUDIO_OUTPUT_DEVICE,  # static.AUDIO_OUTPUT_DEVICE
                                     )

        self.streambuffer = bytes(0)
        self.audio_writing_to_stream = False
        # --------------------------------------------START DECODER THREAD

        DECODER_THREAD = threading.Thread(target=self.receive, name="DECODER_THREAD")
        DECODER_THREAD.start()

        PLAYBACK_THREAD = threading.Thread(target=self.play_audio, name="PLAYBACK_THREAD")
        PLAYBACK_THREAD.start()

        self.fft_data = bytes()
        FFT_THREAD = threading.Thread(target=self.calculate_fft, name="FFT_THREAD")
        FFT_THREAD.start()

        # --------------------------------------------CONFIGURE HAMLIB
        # my_rig.set_ptt(Hamlib.RIG_PTT_RIG,0)
        # my_rig.set_ptt(Hamlib.RIG_PTT_SERIAL_DTR,0)
        # my_rig.set_ptt(Hamlib.RIG_PTT_SERIAL_RTS,1)
        #self.my_rig.set_conf("dtr_state", "OFF")
        #my_rig.set_conf("rts_state", "OFF")
        #self.my_rig.set_conf("ptt_type", "RTS")
        #my_rig.set_conf("ptt_type", "RIG_PTT_SERIAL_RTS")

        # try to init hamlib
        try:
            Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)
            self.my_rig = Hamlib.Rig(int(static.HAMLIB_DEVICE_ID))
            self.my_rig.set_conf("rig_pathname", static.HAMLIB_DEVICE_PORT)
            self.my_rig.set_conf("retry", "5")
            self.my_rig.set_conf("serial_speed", static.HAMLIB_SERIAL_SPEED)
            self.my_rig.set_conf("serial_handshake", "None")
            self.my_rig.set_conf("stop_bits", "1")
            self.my_rig.set_conf("data_bits", "8")

            if static.HAMLIB_PTT_TYPE == 'RIG':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_RIG

            elif static.HAMLIB_PTT_TYPE == 'DTR-H':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_DTR
                self.my_rig.set_conf("dtr_state", "HIGH")
                self.my_rig.set_conf("ptt_type", "DTR")

            elif static.HAMLIB_PTT_TYPE == 'DTR-L':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_DTR
                self.my_rig.set_conf("dtr_state", "LOW")
                self.my_rig.set_conf("ptt_type", "DTR")

            elif static.HAMLIB_PTT_TYPE == 'RTS':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_RTS
                self.my_rig.set_conf("dtr_state", "OFF")
                self.my_rig.set_conf("ptt_type", "RTS")

            elif static.HAMLIB_PTT_TYPE == 'PARALLEL':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_PARALLEL

            elif static.HAMLIB_PTT_TYPE == 'MICDATA':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_RIG_MICDATA

            elif static.HAMLIB_PTT_TYPE == 'CM108':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_CM108

            else:  # static.HAMLIB_PTT_TYPE == 'RIG_PTT_NONE':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_NONE

            self.my_rig.open()
            atexit.register(self.my_rig.close)

            # set rig mode to USB
            self.my_rig.set_mode(Hamlib.RIG_MODE_USB)

            # start thread for getting hamlib data
            HAMLIB_THREAD = threading.Thread(
                target=self.get_radio_stats, name="HAMLIB_THREAD")
            HAMLIB_THREAD.start()

        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("can't open rig")
            sys.exit("hamlib error")


# --------------------------------------------------------------------------------------------------------

    def ptt_and_wait(self, state):
        static.PTT_STATE = state

        if state:

            self.my_rig.set_ptt(self.hamlib_ptt_type, 1)
            # rigctld.ptt_enable()
            ptt_toggle_timeout = time.time() + 0.5
            while time.time() < ptt_toggle_timeout:
                pass

        else:

            ptt_toggle_timeout = time.time() + 0.5
            while time.time() < ptt_toggle_timeout:
                pass

            self.my_rig.set_ptt(self.hamlib_ptt_type, 0)
            # rigctld.ptt_disable()

        return False

    def play_audio(self):

        while True:
            time.sleep(0.01)

            # while len(self.streambuffer) > 0:
            #    time.sleep(0.01)
            if len(self.streambuffer) > 0 and self.audio_writing_to_stream:
                self.streambuffer = bytes(self.streambuffer)

                # we need t wait a little bit until the buffer is filled. If we are not waiting, we are sending empty data
                time.sleep(0.1)
                self.stream_tx.write(self.streambuffer)
                # clear stream buffer after sending
                self.streambuffer = bytes()

            self.audio_writing_to_stream = False
# --------------------------------------------------------------------------------------------------------

    def transmit_signalling(self, data_out, count):
        state_before_transmit = static.CHANNEL_STATE
        static.CHANNEL_STATE = 'SENDING_SIGNALLING'
        # print(static.CHANNEL_STATE)
        freedv_signalling_mode = 14
        
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(freedv_signalling_mode)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_per_frame = bytes_per_frame - 2
        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)
        n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(freedv)
        n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(freedv)

        mod_out = ctypes.c_short * n_tx_modem_samples
        mod_out = mod_out()
        mod_out_preamble = ctypes.c_short * n_tx_preamble_modem_samples
        mod_out_preamble = mod_out_preamble()
        mod_out_postamble = ctypes.c_short * n_tx_postamble_modem_samples
        mod_out_postamble = mod_out_postamble()

        buffer = bytearray(payload_per_frame)
        # set buffersize to length of data which will be send
        buffer[:len(data_out)] = data_out

        crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
        # convert crc to 2 byte hex string
        crc = crc.value.to_bytes(2, byteorder='big')
        buffer += crc        # append crc16 to buffer
        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)

        self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        # modulate DATA and safe it into mod_out pointer
        self.c_lib.freedv_rawdatatx(freedv, mod_out, data)
        self.c_lib.freedv_rawdatapostambletx(freedv, mod_out_postamble)

        self.streambuffer = bytearray()
        self.streambuffer += bytes(mod_out_preamble)
        self.streambuffer += bytes(mod_out)
        self.streambuffer += bytes(mod_out_postamble)

        converted_audio = audioop.ratecv(self.streambuffer, 2, 1, self.MODEM_SAMPLE_RATE, self.AUDIO_SAMPLE_RATE_TX, None)
        self.streambuffer = bytes(converted_audio[0])
        # append frame again with as much as in count defined
        for i in range(1, count):
            self.streambuffer += bytes(converted_audio[0])


        while self.ptt_and_wait(True):
            pass
            
        # start writing audio data to audio stream    
        self.audio_writing_to_stream = True

        # wait until audio has been processed
        while self.audio_writing_to_stream:
            time.sleep(0.01)
            static.CHANNEL_STATE = 'SENDING_SIGNALLING'

        self.ptt_and_wait(False)
        
        # we have a problem with the receiving state
        ##static.CHANNEL_STATE = state_before_transmit
        if state_before_transmit != 'RECEIVING_DATA':
            static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'
        else:
            static.CHANNEL_STATE = state_before_transmit

        self.c_lib.freedv_close(freedv)
        
        return True
# --------------------------------------------------------------------------------------------------------
   # GET ARQ BURST FRAME VOM BUFFER AND MODULATE IT

    def transmit_arq_burst(self, mode, frames):

        # we could place this timing part inside the modem...
        # lets see if this is a good idea..
        # we need to update our timeout timestamp

        state_before_transmit = static.CHANNEL_STATE
        static.CHANNEL_STATE = 'SENDING_DATA'

        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(mode)

        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        #get n_tx_modem_samples which defines the size of the modulation object
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)
        n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(freedv)
        n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(freedv)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_per_frame = bytes_per_frame - 2
        
        
        mod_out = ctypes.c_short * n_tx_modem_samples
        mod_out = mod_out()

        mod_out_preamble = ctypes.c_short * n_tx_preamble_modem_samples
        mod_out_preamble = mod_out_preamble()

        mod_out_postamble = ctypes.c_short * n_tx_postamble_modem_samples
        mod_out_postamble = mod_out_postamble()

        self.streambuffer = bytearray()
        self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        self.streambuffer += bytes(mod_out_preamble)


        # loop through list of frames per burst
        for n in range(0, len(frames)):

            # create TX buffer
                buffer = bytearray(payload_per_frame)
                # set buffersize to length of data which will be send
                buffer[:len(frames[n])] = frames[n]

                crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
                # convert crc to 2 byte hex string
                crc = crc.value.to_bytes(2, byteorder='big')
                buffer += crc        # append crc16 to buffer
                data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)

                # modulate DATA and safe it into mod_out pointer
                self.c_lib.freedv_rawdatatx(freedv, mod_out, data)
                self.streambuffer += bytes(mod_out)

        self.c_lib.freedv_rawdatapostambletx(freedv, mod_out_postamble)
        self.streambuffer += bytes(mod_out_postamble)

        converted_audio = audioop.ratecv(self.streambuffer, 2, 1, self.MODEM_SAMPLE_RATE, self.AUDIO_SAMPLE_RATE_TX, None)
        self.streambuffer = bytes(converted_audio[0])

        # -------------- transmit audio

        while self.ptt_and_wait(True):
            pass
        # this triggers writing buffer to audio stream
        # this way we are able to run this non blocking
        # this needs to be optimized!
        self.audio_writing_to_stream = True

        # wait until audio has been processed
        while self.audio_writing_to_stream:
            time.sleep(0.01)
            static.CHANNEL_STATE = 'SENDING_DATA'

        static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

        self.ptt_and_wait(False)

        # close codec2 instance
        self.c_lib.freedv_close(freedv)
        
        return True
# --------------------------------------------------------------------------------------------------------

    def receive(self):
        
        freedv_mode_datac0 = 14
        freedv_mode_datac1 = 10
        freedv_mode_datac3 = 12
        
        # DATAC0
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        datac0_freedv = self.c_lib.freedv_open(freedv_mode_datac0)
        self.c_lib.freedv_get_bits_per_modem_frame(datac0_freedv)
        datac0_bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(datac0_freedv)/8)
        datac0_n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(datac0_freedv)

        # bytes_per_frame
        datac0_bytes_out = (ctypes.c_ubyte * datac0_bytes_per_frame)
        datac0_bytes_out = datac0_bytes_out()  # get pointer from bytes_out

        self.c_lib.freedv_set_frames_per_burst(datac0_freedv, 1)
        datac0_modem_stats_snr = c_float()
        datac0_modem_stats_sync = c_int()
        datac0_buffer = bytes()

        static.FREEDV_SIGNALLING_BYTES_PER_FRAME = datac0_bytes_per_frame
        static.FREEDV_SIGNALLING_PAYLOAD_PER_FRAME = datac0_bytes_per_frame - 2

        # DATAC1
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        datac1_freedv = self.c_lib.freedv_open(freedv_mode_datac1)
        datac1_bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(datac1_freedv)/8)
        datac1_n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(datac1_freedv)
        # bytes_per_frame
        datac1_bytes_out = (ctypes.c_ubyte * datac1_bytes_per_frame)
        datac1_bytes_out = datac1_bytes_out()  # get pointer from bytes_out
        self.c_lib.freedv_set_frames_per_burst(datac1_freedv, 1)
        datac1_modem_stats_snr = c_float()
        datac1_modem_stats_sync = c_int()
        datac1_buffer = bytes()

        # DATAC3
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        datac3_freedv = self.c_lib.freedv_open(freedv_mode_datac3)
        datac3_bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(datac3_freedv)/8)
        datac3_n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(datac3_freedv)
        # bytes_per_frame
        datac3_bytes_out = (ctypes.c_ubyte * datac3_bytes_per_frame)
        datac3_bytes_out = datac3_bytes_out()  # get pointer from bytes_out
        self.c_lib.freedv_set_frames_per_burst(datac3_freedv, 1)
        datac3_modem_stats_snr = c_float()
        datac3_modem_stats_sync = c_int()
        datac3_buffer = bytes()

        '''
        if mode == static.ARQ_DATA_CHANNEL_MODE:
            static.FREEDV_DATA_BYTES_PER_FRAME = bytes_per_frame
            static.FREEDV_DATA_PAYLOAD_PER_FRAME = bytes_per_frame - 2

            self.c_lib.freedv_set_frames_per_burst(freedv, 0)
        else:
            #pass
            self.c_lib.freedv_set_frames_per_burst(freedv, 0)
        '''
        fft_buffer = bytes()
        while True:

            '''
            # refresh vars, so the correct parameters of the used mode are set
            if mode == static.ARQ_DATA_CHANNEL_MODE:
                static.FREEDV_DATA_BYTES_PER_FRAME = bytes_per_frame
                static.FREEDV_DATA_PAYLOAD_PER_FRAME = bytes_per_frame - 2
            '''

            data_in = bytes()
            data_in = self.stream_rx.read(self.AUDIO_CHUNKS,  exception_on_overflow=False)
            #self.fft_data = data_in
            data_in = audioop.ratecv(data_in, 2, 1, self.AUDIO_SAMPLE_RATE_RX, self.MODEM_SAMPLE_RATE, None)
            data_in = data_in[0]  # .rstrip(b'\x00')
            #self.fft_data = data_in

            # we need to set nin * 2 beause of byte size in array handling
            datac0_nin = self.c_lib.freedv_nin(datac0_freedv) * 2
            datac1_nin = self.c_lib.freedv_nin(datac1_freedv) * 2
            datac3_nin = self.c_lib.freedv_nin(datac3_freedv) * 2

            # refill buffer only if every mode has worked with its data
            if (len(datac0_buffer) < (datac0_nin*2)) and (len(datac1_buffer) < (datac1_nin*2)) and (len(datac3_buffer) < (datac3_nin*2)):
                datac0_buffer += data_in
                datac1_buffer += data_in
                datac3_buffer += data_in
                
            # refill fft_data buffer so we can plot a fft
            if len(self.fft_data) < 1024:
                self.fft_data += data_in


            # DECODING DATAC0
            if len(datac0_buffer) >= (datac0_nin):

                datac0_audio = datac0_buffer[:datac0_nin]
                datac0_buffer = datac0_buffer[datac0_nin:]
                # print(len(datac0_audio))
                self.c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), datac0_bytes_out, datac0_audio]
                nbytes = self.c_lib.freedv_rawdatarx(datac0_freedv, datac0_bytes_out, datac0_audio)  # demodulate audio
                sync = self.c_lib.freedv_get_rx_status(datac0_freedv)
                if sync != 0 and nbytes != 0:

                    # calculate snr and scatter
                    self.get_scatter(datac0_freedv)
                    self.calculate_snr(datac0_freedv)

                    datac0_task = threading.Thread(target=self.process_data, args=[datac0_bytes_out, datac0_freedv, datac0_bytes_per_frame])
                    #datac0_task.start()
                    self.process_data(datac0_bytes_out, datac0_freedv, datac0_bytes_per_frame)

            # DECODING DATAC1
            if len(datac1_buffer) >= (datac1_nin):
                datac1_audio = datac1_buffer[:datac1_nin]
                datac1_buffer = datac1_buffer[datac1_nin:]
                # print(len(datac1_audio))
                self.c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), datac1_bytes_out, datac1_audio]
                nbytes = self.c_lib.freedv_rawdatarx(datac1_freedv, datac1_bytes_out, datac1_audio)  # demodulate audio

                sync = self.c_lib.freedv_get_rx_status(datac1_freedv)
                if sync != 0 and nbytes != 0:

                    # calculate snr and scatter
                    self.get_scatter(datac1_freedv)
                    self.calculate_snr(datac1_freedv)

                    datac1_task = threading.Thread(target=self.process_data, args=[datac1_bytes_out, datac1_freedv, datac1_bytes_per_frame])
                    datac1_task.start()
                    #print(bytes(datac1_bytes_out))
                    #self.process_data(datac1_bytes_out, datac1_freedv, datac1_bytes_per_frame)

            # DECODING DATAC3
            if len(datac3_buffer) >= (datac3_nin):
                datac3_audio = datac3_buffer[:datac3_nin]
                datac3_buffer = datac3_buffer[datac3_nin:]
                self.c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), datac3_bytes_out, datac3_audio]
                nbytes = self.c_lib.freedv_rawdatarx(datac3_freedv, datac3_bytes_out, datac3_audio)  # demodulate audio

                sync = self.c_lib.freedv_get_rx_status(datac3_freedv)
                if sync != 0 and nbytes != 0:

                    # calculate snr and scatter
                    #self.get_scatter(datac3_freedv)
                    self.calculate_snr(datac3_freedv)

                    datac3_task = threading.Thread(target=self.process_data, args=[datac3_bytes_out, datac3_freedv, datac3_bytes_per_frame])
                    datac3_task.start()

                # forward data only if broadcast or we are the receiver
                # bytes_out[1:2] == callsign check for signalling frames, bytes_out[6:7] == callsign check for data frames, bytes_out[1:2] == b'\x01' --> broadcasts like CQ
                # we could also create an own function, which returns True. In this case we could add callsign blacklists, whitelists and so on

    def process_data(self, bytes_out, freedv, bytes_per_frame):

        if bytes(bytes_out[1:2]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[6:7]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[1:2]) == b'\x01':


            # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
            frametype = int.from_bytes(bytes(bytes_out[:1]), "big")
            frame = frametype - 10
            n_frames_per_burst = int.from_bytes(bytes(bytes_out[1:2]), "big")

            #self.c_lib.freedv_set_frames_per_burst(freedv_data, n_frames_per_burst);

            if 50 >= frametype >= 10:
                # force, if we don't simulate a loss of the third frame
                force = True
                if frame != 3 or force == True:

                    # send payload data to arq checker without CRC16
                    data_handler.arq_data_received(bytes(bytes_out[:-2]), bytes_per_frame)

                    #print("static.ARQ_RX_BURST_BUFFER.count(None) " + str(static.ARQ_RX_BURST_BUFFER.count(None)))
                    if static.RX_BURST_BUFFER.count(None) <= 1:
                        logging.debug("FULL BURST BUFFER ---> UNSYNC")
                        self.c_lib.freedv_set_sync(freedv, 0)

                else:
                    logging.critical(
                        "---------------------------SIMULATED MISSING FRAME")
                    force = True

            # BURST ACK
            elif frametype == 60:
                logging.debug("ACK RECEIVED....")
                data_handler.burst_ack_received()

            # FRAME ACK
            elif frametype == 61:
                logging.debug("FRAME ACK RECEIVED....")
                data_handler.frame_ack_received()

            # FRAME RPT
            elif frametype == 62:
                logging.debug("REPEAT REQUEST RECEIVED....")
                data_handler.burst_rpt_received(bytes_out[:-2])

            # CQ FRAME
            elif frametype == 200:
                logging.debug("CQ RECEIVED....")
                data_handler.received_cq(bytes_out[:-2])

            # PING FRAME
            elif frametype == 210:
                logging.debug("PING RECEIVED....")
                data_handler.received_ping(bytes_out[:-2])

            # PING ACK
            elif frametype == 211:
                logging.debug("PING ACK RECEIVED....")
                data_handler.received_ping_ack(bytes_out[:-2])

            # ARQ FILE TRANSFER RECEIVED!
            elif frametype == 225:
                logging.debug("ARQ arq_received_data_channel_opener RECEIVED")
                data_handler.arq_received_data_channel_opener(bytes_out[:-2])

            # ARQ CHANNEL IS OPENED
            elif frametype == 226:
                logging.debug("ARQ arq_received_channel_is_open RECEIVED")
                data_handler.arq_received_channel_is_open(bytes_out[:-2])

            # ARQ CONNECT ACK / KEEP ALIVE
            elif frametype == 230:
                logging.debug("BEACON RECEIVED")
                data_handler.received_beacon(bytes_out[:-2])

            else:
                logging.info("OTHER FRAME: " + str(bytes_out[:-2]))
                print(frametype)

            # DO UNSYNC AFTER LAST BURST by checking the frame nums against the total frames per burst
            if frame == n_frames_per_burst:

                logging.debug("LAST FRAME ---> UNSYNC")
                self.c_lib.freedv_set_sync(freedv, 0)  # FORCE UNSYNC


        else:
            # for debugging purposes to receive all data
            pass
            # print(bytes_out[:-2])

    def get_scatter(self, freedv):
        modemStats = MODEMSTATS()
        self.c_lib.freedv_get_modem_extended_stats.restype = None
        self.c_lib.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats))

        scatterdata = []
        scatterdata_small = []
        for i in range(MODEM_STATS_NC_MAX):
            for j in range(MODEM_STATS_NR_MAX):
                # check if odd or not to get every 2nd item for x
                if (j % 2) == 0:
                    xsymbols = round(modemStats.rx_symbols[i][j]/1000)
                    ysymbols = round(modemStats.rx_symbols[i][j+1]/1000)
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
            
            
    def calculate_ber(self, freedv):
        Tbits = self.c_lib.freedv_get_total_bits(freedv)
        Terrs = self.c_lib.freedv_get_total_bit_errors(freedv)

        if Tbits != 0:
            ber = (Terrs / Tbits) * 100
            static.BER = int(ber)

        self.c_lib.freedv_set_total_bit_errors(freedv, 0)
        self.c_lib.freedv_set_total_bits(freedv, 0)

    def calculate_snr(self, freedv):

        modem_stats_snr = c_float()
        modem_stats_sync = c_int()

        self.c_lib.freedv_get_modem_stats(freedv, byref(
            modem_stats_sync), byref(modem_stats_snr))
        modem_stats_snr = modem_stats_snr.value
        try:
            static.SNR = round(modem_stats_snr, 1)
        except:
            static.SNR = 0

    def get_radio_stats(self):
        while True:
            time.sleep(0.1)
            static.HAMLIB_FREQUENCY = int(self.my_rig.get_freq())
            (hamlib_mode, static.HAMLIB_BANDWITH) = self.my_rig.get_mode()
            static.HAMLIB_MODE = Hamlib.rig_strrmode(hamlib_mode)
        #static.HAMLIB_FREQUENCY = rigctld.get_frequency()
        #static.HAMLIB_MODE = rigctld.get_mode()[0]
        #static.HAMLIB_BANDWITH = rigctld.get_mode()[1]

    def calculate_fft(self):
        while True:
            time.sleep(0.01)
            # WE NEED TO OPTIMIZE THIS!
            if len(self.fft_data) >= 1024:
                data_in = self.fft_data
                self.fft_data = bytes()
                
                # https://gist.github.com/ZWMiller/53232427efc5088007cab6feee7c6e4c
                audio_data = np.fromstring(data_in, np.int16)
                # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
                # and make sure it's not imaginary

                try:
                    fftarray = np.fft.rfft(audio_data)
                    

                    
                    # set value 0 to 1 to avoid division by zero
                    fftarray[fftarray == 0] = 1
                    dfft = 10.*np.log10(abs(fftarray))
                    # round data to decrease size
                    dfft = np.around(dfft, 1)
                    dfftlist = dfft.tolist()


                    # send fft only if receiving
                    if static.CHANNEL_STATE == 'RECEIVING_SIGNALLING' or static.CHANNEL_STATE == 'RECEIVING_DATA':
                        #static.FFT = dfftlist[20:100]
                        static.FFT = dfftlist
                    
                except:
                    print("setting fft = 0")
                    # else 0
                    static.FFT = [0] * 400
            else:
                pass
