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
import logging, structlog, log_handler
import time
import threading
import atexit
import numpy as np
import helpers
import static
import data_handler
import re

import codec2

# option for testing miniaudio instead of audioop for sample rate conversion
#import miniaudio


####################################################
# https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time
# https://github.com/DJ2LS/FreeDATA/issues/22
# we need to have a look at this if we want to run this on Windows and MacOS !
# Currently it seems, this is a Linux-only problem

from ctypes import *
from contextlib import contextmanager
import pyaudio

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)
    
# with noalsaerr():
#   p = pyaudio.PyAudio()
######################################################

# try importing hamlib    
try:
    # get python version
    python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])

    # installation path for Ubuntu 20.04 LTS python modules
    sys.path.append('/usr/local/lib/python'+ python_version +'/site-packages')
    # installation path for Ubuntu 20.10 +
    sys.path.append('/usr/local/lib/')
    import Hamlib
            
    # https://stackoverflow.com/a/4703409
    hamlib_version = re.findall(r"[-+]?\d*\.?\d+|\d+", Hamlib.cvar.hamlib_version)    
    hamlib_version = float(hamlib_version[0])
            
    min_hamlib_version = 4.1
    if hamlib_version > min_hamlib_version:
        structlog.get_logger("structlog").info("[TNC] Hamlib found", version=hamlib_version)
    else:
        structlog.get_logger("structlog").warning("[TNC] Hamlib outdated", found=hamlib_version, recommend=min_hamlib_version)
except Exception as e:
    structlog.get_logger("structlog").critical("[TNC] Hamlib not found", error=e)


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
        self.AUDIO_FRAMES_PER_BUFFER_RX = 8192  #8192
        self.AUDIO_FRAMES_PER_BUFFER_TX = 8     #8192 Lets to some tests with very small chunks for TX
        self.AUDIO_CHUNKS = 48 #8 * (self.AUDIO_SAMPLE_RATE_RX/self.MODEM_SAMPLE_RATE) #48
        self.AUDIO_CHANNELS = 1
        
        # small hack for initializing codec2 via codec2.py module
        # TODO: we need to change the entire modem module to integrate codec2 module
        self.c_lib = codec2.api
        
        '''        
        # -------------------------------------------- LOAD FREEDV
        try:
            # we check at first for libcodec2 compiled from source
            # this happens, if we want to run it beeing build in a dev environment
            # libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so.1.0"
            libname = pathlib.Path("codec2/build_linux/src/libcodec2.so.1.0")
            if libname.is_file():
                self.c_lib = ctypes.CDLL(libname)
                structlog.get_logger("structlog").info("[TNC] Codec2 found", path=libname, origin="source")
            else:
                structlog.get_logger("structlog").critical("[TNC] Codec2 not loaded")
                raise UnboundLocalError

        except:
            # this is the normal behavior. Run codec2 from lib folder
            #libname = pathlib.Path().absolute() / "lib/codec2/linux/libcodec2.so.1.0"
            libname = pathlib.Path("lib/codec2/linux/libcodec2.so.1.0")
            if libname.is_file():
                self.c_lib = ctypes.CDLL(libname)
                structlog.get_logger("structlog").info("[TNC] Codec2 found", path=libname, origin="precompiled")
            else:
                structlog.get_logger("structlog").critical("[TNC] Codec2 not found")
        '''
        '''
        # --------------------------------------------CTYPES FUNCTION INIT
        # TODO: WE STILL HAVE SOME MISSING FUNCTIONS!

        self.c_lib.freedv_open.argype = [c_int]
        self.c_lib.freedv_open.restype = c_void_p

        self.c_lib.freedv_nin.argtype = [c_void_p]
        self.c_lib.freedv_nin.restype = c_int

        self.c_lib.freedv_rawdatarx.argtype = [c_void_p, c_char_p, c_char_p]
        self.c_lib.freedv_rawdatarx.restype = c_int

        self.c_lib.freedv_get_sync.argtype = [c_void_p]
        self.c_lib.freedv_get_sync.restype = c_int

        self.c_lib.freedv_get_bits_per_modem_frame.argtype = [c_void_p]
        self.c_lib.freedv_get_bits_per_modem_frame.restype = c_int

        self.c_lib.freedv_set_frames_per_burst.argtype = [c_void_p, c_int]
        self.c_lib.freedv_set_frames_per_burst.restype = c_int
        '''

        # --------------------------------------------CREATE PYAUDIO  INSTANCE
        try:
        # we need to "try" this, because sometimes libasound.so isn't in the default place                   
            # try to supress error messages
            with noalsaerr(): # https://github.com/DJ2LS/FreeDATA/issues/22
                self.p = pyaudio.PyAudio()
        # else do it the default way
        except:
            self.p = pyaudio.PyAudio()
        atexit.register(self.p.terminate)
        # --------------------------------------------OPEN AUDIO CHANNEL RX
        # optional auto selection of loopback device if using in testmode
        if static.AUDIO_INPUT_DEVICE == -2:
            loopback_list = []
            for dev in range(0,self.p.get_device_count()):
                if 'Loopback: PCM' in self.p.get_device_info_by_index(dev)["name"]:
                    loopback_list.append(dev)
            if len(loopback_list) >= 2:
                AUDIO_INPUT_DEVICE = loopback_list[0] #0  = RX   1 = TX
                print(f"loopback_list rx: {loopback_list}", file=sys.stderr)
        
        
        self.stream_rx = self.p.open(format=pyaudio.paInt16,
                                     channels=self.AUDIO_CHANNELS,
                                     rate=self.AUDIO_SAMPLE_RATE_RX,
                                     frames_per_buffer=self.AUDIO_FRAMES_PER_BUFFER_RX,
                                     input=True,
                                     input_device_index=static.AUDIO_INPUT_DEVICE
                                     )
        # --------------------------------------------OPEN AUDIO CHANNEL TX
        # optional auto selection of loopback device if using in testmode        
        if static.AUDIO_OUTPUT_DEVICE == -2:
            loopback_list = []
            for dev in range(0,self.p.get_device_count()):
                if 'Loopback: PCM' in self.p.get_device_info_by_index(dev)["name"]:
                    loopback_list.append(dev)
            if len(loopback_list) >= 2:
                static.AUDIO_OUTPUT_DEVICE = loopback_list[1] #0  = RX   1 = TX
                print(f"loopback_list tx: {loopback_list}", file=sys.stderr)
        
        self.stream_tx = self.p.open(format=pyaudio.paInt16,
                                     channels=self.AUDIO_CHANNELS,
                                     rate=self.AUDIO_SAMPLE_RATE_TX,
                                     frames_per_buffer=self.AUDIO_FRAMES_PER_BUFFER_TX,  # n_nom_modem_samples
                                     output=True,
                                     output_device_index=static.AUDIO_OUTPUT_DEVICE,  # static.AUDIO_OUTPUT_DEVICE
                                     )

        self.streambuffer = bytes(0)
        self.audio_writing_to_stream = False
        # --------------------------------------------START DECODER THREAD

        DECODER_THREAD = threading.Thread(target=self.receive, name="DECODER_THREAD")
        DECODER_THREAD.start()

        #PLAYBACK_THREAD = threading.Thread(target=self.play_audio, name="PLAYBACK_THREAD")
        #PLAYBACK_THREAD.start()

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

            # get devicenumber by looking for deviceobject in Hamlib module
            try:
                devicenumber = getattr(Hamlib, static.HAMLIB_DEVICE_ID)
            except:
                structlog.get_logger("structlog").error("[DMN] Hamlib: rig not supported...")
                devicenumber = 0
                
            self.my_rig = Hamlib.Rig(int(devicenumber))
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
            HAMLIB_THREAD = threading.Thread(target=self.get_radio_stats, name="HAMLIB_THREAD")
            HAMLIB_THREAD.start()

        except:
            structlog.get_logger("structlog").error("[TNC] Hamlib - can't open rig", e=sys.exc_info()[0])


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

    # --------------------------------------------------------------------------------------------------------

    def transmit_signalling(self, data_out, count):
        state_before_transmit = static.CHANNEL_STATE
        static.CHANNEL_STATE = 'SENDING_SIGNALLING'

        freedv_signalling_mode = 14

        freedv = cast(self.c_lib.freedv_open(freedv_signalling_mode), c_void_p)
        
        self.c_lib.freedv_set_clip(freedv, 1)
        self.c_lib.freedv_set_tx_bpf(freedv, 1)
              
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_per_frame = bytes_per_frame - 2
        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)
        n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(freedv)
        n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(freedv)

        mod_out = create_string_buffer(n_tx_modem_samples * 2)
        mod_out_preamble = create_string_buffer(n_tx_preamble_modem_samples * 2)
        mod_out_postamble = create_string_buffer(n_tx_postamble_modem_samples * 2)

        buffer = bytearray(payload_per_frame)
        # set buffersize to length of data which will be send
        buffer[:len(data_out)] = data_out

        crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
        # convert crc to 2 byte hex string
        crc = crc.value.to_bytes(2, byteorder='big')
        buffer += crc        # append crc16 to buffer
        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
        
        # modulate DATA and safe it into mod_out pointer
        self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble)
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
        
        # set channel state   
        static.CHANNEL_STATE = 'SENDING_SIGNALLING'       
            
        # start writing audio data to audio stream  
        self.stream_tx.write(self.streambuffer)
        
        # set ptt back to false
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

        freedv = cast(self.c_lib.freedv_open(mode), c_void_p)
        self.c_lib.freedv_set_clip(freedv, 1)
        self.c_lib.freedv_set_tx_bpf(freedv, 1)
              
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_per_frame = bytes_per_frame - 2
        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)
        n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(freedv)
        n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(freedv)

        mod_out = create_string_buffer(n_tx_modem_samples * 2)
        mod_out_preamble = create_string_buffer(n_tx_preamble_modem_samples * 2)
        mod_out_postamble = create_string_buffer(n_tx_postamble_modem_samples * 2)

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

        # set channel state
        static.CHANNEL_STATE = 'SENDING_DATA'
        
        # write audio to stream
        self.stream_tx.write(self.streambuffer)
        
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

        datac0_freedv = cast(self.c_lib.freedv_open(freedv_mode_datac0), c_void_p)
        self.c_lib.freedv_get_bits_per_modem_frame(datac0_freedv)
        datac0_bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(datac0_freedv)/8)
        datac0_n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(datac0_freedv)
        datac0_bytes_out = create_string_buffer(datac0_bytes_per_frame * 2)
        self.c_lib.freedv_set_frames_per_burst(datac0_freedv, 1)
        datac0_modem_stats_snr = c_float()
        datac0_modem_stats_sync = c_int()
        datac0_buffer = bytes()

        static.FREEDV_SIGNALLING_BYTES_PER_FRAME = datac0_bytes_per_frame
        static.FREEDV_SIGNALLING_PAYLOAD_PER_FRAME = datac0_bytes_per_frame - 2

        # DATAC1
        datac1_freedv = cast(self.c_lib.freedv_open(freedv_mode_datac1), c_void_p)
        datac1_bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(datac1_freedv)/8)
        datac1_n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(datac1_freedv)
        datac1_bytes_out = create_string_buffer(datac1_bytes_per_frame * 2)
        self.c_lib.freedv_set_frames_per_burst(datac1_freedv, 0)
        datac1_modem_stats_snr = c_float()
        datac1_modem_stats_sync = c_int()
        datac1_buffer = bytes()

        # DATAC3
        datac3_freedv = cast(self.c_lib.freedv_open(freedv_mode_datac3), c_void_p)
        datac3_bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(datac3_freedv)/8)
        datac3_n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(datac3_freedv)
        datac3_bytes_out = create_string_buffer(datac3_bytes_per_frame * 2)
        self.c_lib.freedv_set_frames_per_burst(datac3_freedv, 0)
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

            data_in = bytes()
            data_in = self.stream_rx.read(self.AUDIO_CHUNKS,  exception_on_overflow=False)
            data_in = audioop.ratecv(data_in, 2, 1, self.AUDIO_SAMPLE_RATE_RX, self.MODEM_SAMPLE_RATE, None)
            data_in = data_in[0]#.rstrip(b'\x00')
            
            # we need to set nin * 2 beause of byte size in array handling
            datac0_nin = self.c_lib.freedv_nin(datac0_freedv) * 2
            datac1_nin = self.c_lib.freedv_nin(datac1_freedv) * 2
            datac3_nin = self.c_lib.freedv_nin(datac3_freedv) * 2

            '''
            # refill buffer only if every mode has worked with its data
            if (len(datac0_buffer) < (datac0_nin)) and (len(datac1_buffer) < (datac1_nin)) and (len(datac3_buffer) < (datac3_nin)):
                
                datac0_buffer += data_in
                datac1_buffer += data_in
                datac3_buffer += data_in
                
            '''    
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
                nbytes = self.c_lib.freedv_rawdatarx(datac0_freedv, datac0_bytes_out, datac0_audio)  # demodulate audio
                sync = self.c_lib.freedv_get_rx_status(datac0_freedv)

                self.get_scatter(datac0_freedv)
                
                if sync != 0 and nbytes != 0:
                    print("----------DECODE----------------")
                                            
                    # calculate snr and scatter
                    self.get_scatter(datac0_freedv)
                    self.calculate_snr(datac0_freedv)
                    
                    datac0_task = threading.Thread(target=self.process_data, args=[datac0_bytes_out, datac0_freedv, datac0_bytes_per_frame])
                    datac0_task.start()


            # DECODING DATAC1
            if len(datac1_buffer) >= (datac1_nin):
                datac1_audio = datac1_buffer[:datac1_nin]
                datac1_buffer = datac1_buffer[datac1_nin:]
                nbytes = self.c_lib.freedv_rawdatarx(datac1_freedv, datac1_bytes_out, datac1_audio)  # demodulate audio

                sync = self.c_lib.freedv_get_rx_status(datac1_freedv)
                if sync != 0 and nbytes != 0:
                    print("----------DECODE----------------")
                    frame = int.from_bytes(bytes(datac1_bytes_out[:1]), "big") - 10
                    n_frames_per_burst = int.from_bytes(bytes(datac1_bytes_out[1:2]), "big")
                    print("frame: {0}, N_frames_per_burst: {1}".format(frame, n_frames_per_burst))

                    # calculate snr and scatter
                    self.get_scatter(datac1_freedv)
                    self.calculate_snr(datac1_freedv)

                    datac1_task = threading.Thread(target=self.process_data, args=[datac1_bytes_out, datac1_freedv, datac1_bytes_per_frame])
                    datac1_task.start()


            # DECODING DATAC3
            if len(datac3_buffer) >= (datac3_nin):
                datac3_audio = datac3_buffer[:datac3_nin]
                datac3_buffer = datac3_buffer[datac3_nin:]
                nbytes = self.c_lib.freedv_rawdatarx(datac3_freedv, datac3_bytes_out, datac3_audio)  # demodulate audio

                sync = self.c_lib.freedv_get_rx_status(datac3_freedv)
                if sync != 0 and nbytes != 0:
                    print("----------DECODE----------------")
                    # calculate snr and scatter
                    self.get_scatter(datac3_freedv)
                    self.calculate_snr(datac3_freedv)

                    datac3_task = threading.Thread(target=self.process_data, args=[datac3_bytes_out, datac3_freedv, datac3_bytes_per_frame])
                    datac3_task.start()

    # forward data only if broadcast or we are the receiver
    # bytes_out[1:2] == callsign check for signalling frames, 
    # bytes_out[6:7] == callsign check for data frames, 
    # bytes_out[1:2] == b'\x01' --> broadcasts like CQ
    # we could also create an own function, which returns True. 
    def process_data(self, bytes_out, freedv, bytes_per_frame):

        if bytes(bytes_out[1:2]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[6:7]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[1:2]) == b'\x01':

            # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
            frametype = int.from_bytes(bytes(bytes_out[:1]), "big")
            frame = frametype - 10
            n_frames_per_burst = int.from_bytes(bytes(bytes_out[1:2]), "big")
            #self.c_lib.freedv_set_frames_per_burst(freedv, n_frames_per_burst);

            #frequency_offset = self.get_frequency_offset(freedv)
            #print("Freq-Offset: " + str(frequency_offset))
            
            if 50 >= frametype >= 10:
                # force = True, if we don't simulate a loss of the third frame, else force = False
                force = True
                if frame != 3 or force:

                    # send payload data to arq checker without CRC16
                    data_handler.arq_data_received(bytes(bytes_out[:-2]), bytes_per_frame)

                    #print("static.ARQ_RX_BURST_BUFFER.count(None) " + str(static.ARQ_RX_BURST_BUFFER.count(None)))
                    if static.RX_BURST_BUFFER.count(None) <= 1:
                        logging.debug("FULL BURST BUFFER ---> UNSYNC")
                        self.c_lib.freedv_set_sync(freedv, 0)

                else:
                    logging.critical("-------------SIMULATED MISSING FRAME")
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
                frequency_offset = self.get_frequency_offset(freedv)
                #print("Freq-Offset: " + str(frequency_offset))
                data_handler.received_ping(bytes_out[:-2], frequency_offset)
                

            # PING ACK
            elif frametype == 211:
                logging.debug("PING ACK RECEIVED....")
                # early detection of frequency offset
                #frequency_offset = int.from_bytes(bytes(bytes_out[9:11]), "big", signed=True)
                #print("Freq-Offset: " + str(frequency_offset))
                #current_frequency = self.my_rig.get_freq()
                #corrected_frequency = current_frequency + frequency_offset
                # temporarely disabled this feature, beacuse it may cause some confusion.
                # we also have problems if we are operating at band bordes like 7.000Mhz
                # If we get a corrected frequency less 7.000 Mhz, Ham Radio devices will not transmit...
                #self.my_rig.set_vfo(Hamlib.RIG_VFO_A)
                #self.my_rig.set_freq(Hamlib.RIG_VFO_A, corrected_frequency)
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
                structlog.get_logger("structlog").warning("[TNC] ARQ - other frame type", frametype=frametype)

            # DO UNSYNC AFTER LAST BURST by checking the frame nums against the total frames per burst
            if frame == n_frames_per_burst:
                logging.info("LAST FRAME ---> UNSYNC")
                self.c_lib.freedv_set_sync(freedv, 0)  # FORCE UNSYNC


        else:
            # for debugging purposes to receive all data
            structlog.get_logger("structlog").debug("[TNC] Unknown frame received", frame=bytes_out[:-2])


    def get_frequency_offset(self, freedv):
        modemStats = MODEMSTATS()
        self.c_lib.freedv_get_modem_extended_stats.restype = None
        self.c_lib.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats))
        offset = round(modemStats.foff) * (-1)
        static.FREQ_OFFSET = offset
        return offset
        
        
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

                    static.FFT = dfftlist[10:180] #200 --> bandwith 3000    
                except:
                    
                    structlog.get_logger("structlog").debug("[TNC] Setting fft=0")
                    # else 0
                    static.FFT = [0] * 400
            else:
                pass

