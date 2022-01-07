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
import queue
import codec2

if static.HAMLIB_USE_RIGCTL:
    structlog.get_logger("structlog").warning("using rigctl....")
    import rigctl as rig
else:
    structlog.get_logger("structlog").warning("using rig.......")
    import rig

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

# init FIFO queue to store received frames in
MODEM_RECEIVED_QUEUE = queue.Queue()
MODEM_TRANSMIT_QUEUE = queue.Queue()
static.TRANSMITTING = False

class RF():

    def __init__(self):
        self.AUDIO_SAMPLE_RATE_RX = 48000
        self.AUDIO_SAMPLE_RATE_TX = 48000
        self.MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
        self.AUDIO_FRAMES_PER_BUFFER_RX = 2400*2  #8192
        self.AUDIO_FRAMES_PER_BUFFER_TX = 2400*2     #8192 Lets to some tests with very small chunks for TX
        self.AUDIO_CHUNKS = 48 #8 * (self.AUDIO_SAMPLE_RATE_RX/self.MODEM_SAMPLE_RATE) #48
        self.AUDIO_CHANNELS = 1
        
        # make sure our resampler will work
        assert (self.AUDIO_SAMPLE_RATE_RX / self.MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48
        
        # small hack for initializing codec2 via codec2.py module
        # TODO: we need to change the entire modem module to integrate codec2 module
        self.c_lib = codec2.api
        self.resampler = codec2.resampler()

        self.modem_transmit_queue = MODEM_TRANSMIT_QUEUE
        self.modem_received_queue = MODEM_RECEIVED_QUEUE

        # init FIFO queue to store modulation out in
        self.modoutqueue = queue.Queue()
        
        # define fft_data buffer
        self.fft_data = bytes()
                
        # open codec2 instance        
        self.datac0_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC0), c_void_p)
        self.datac0_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac0_freedv)/8)
        self.datac0_payload_per_frame = self.datac0_bytes_per_frame -2
        self.datac0_n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(self.datac0_freedv)
        self.datac0_n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(self.datac0_freedv)
        self.datac0_n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(self.datac0_freedv)
        self.datac0_n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(self.datac0_freedv)
        self.datac0_bytes_out = create_string_buffer(self.datac0_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac0_freedv,1)
        self.datac0_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER_RX)

        self.datac1_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC1), c_void_p)
        self.datac1_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac1_freedv)/8)
        self.datac1_bytes_out = create_string_buffer(self.datac1_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac1_freedv,1)
        self.datac1_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER_RX)

        self.datac3_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC3), c_void_p)
        self.datac3_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac3_freedv)/8)
        self.datac3_bytes_out = create_string_buffer(self.datac3_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac3_freedv,1)
        self.datac3_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER_RX)

        # initial nin values        
        self.datac0_nin = codec2.api.freedv_nin(self.datac0_freedv)               
        self.datac1_nin = codec2.api.freedv_nin(self.datac1_freedv)               
        self.datac3_nin = codec2.api.freedv_nin(self.datac3_freedv)
        
        # --------------------------------------------CREATE PYAUDIO INSTANCE
        try:
        # we need to "try" this, because sometimes libasound.so isn't in the default place                   
            # try to supress error messages
            with noalsaerr(): # https://github.com/DJ2LS/FreeDATA/issues/22
                self.p = pyaudio.PyAudio()
        # else do it the default way
        except:
            self.p = pyaudio.PyAudio()
        atexit.register(self.p.terminate)
        
        # --------------------------------------------OPEN RX AUDIO CHANNEL
        # optional auto selection of loopback device if using in testmode
        if static.AUDIO_INPUT_DEVICE == -2:
            loopback_list = []
            for dev in range(0,self.p.get_device_count()):
                if 'Loopback: PCM' in self.p.get_device_info_by_index(dev)["name"]:
                    loopback_list.append(dev)
            if len(loopback_list) >= 2:
                static.AUDIO_INPUT_DEVICE = loopback_list[0] #0  = RX
                static.AUDIO_OUTPUT_DEVICE = loopback_list[1] #1 = TX
                print(f"loopback_list rx: {loopback_list}", file=sys.stderr)
                
        self.audio_stream = self.p.open(format=pyaudio.paInt16,
                                     channels=self.AUDIO_CHANNELS,
                                     rate=self.AUDIO_SAMPLE_RATE_RX,
                                     frames_per_buffer=self.AUDIO_FRAMES_PER_BUFFER_RX,
                                     input=True,
                                     output=True,
                                     input_device_index=static.AUDIO_INPUT_DEVICE,
                                     output_device_index=static.AUDIO_OUTPUT_DEVICE,
                                     stream_callback=self.audio_callback
                                     )
        try:                        
            structlog.get_logger("structlog").debug("[TNC] starting pyaudio callback")
            self.audio_stream.start_stream()
        except Exception as e:
            structlog.get_logger("structlog").error("[TNC] starting pyaudio callback failed", e=e)

        # --------------------------------------------INIT AND OPEN HAMLIB
        self.hamlib = rig.radio()
        self.hamlib.open_rig(devicename=static.HAMLIB_DEVICE_NAME, deviceport=static.HAMLIB_DEVICE_PORT, hamlib_ptt_type=static.HAMLIB_PTT_TYPE, serialspeed=static.HAMLIB_SERIAL_SPEED, pttport=static.HAMLIB_PTT_PORT, data_bits=static.HAMLIB_DATA_BITS, stop_bits=static.HAMLIB_STOP_BITS, handshake=static.HAMLIB_HANDSHAKE)
        
        # --------------------------------------------START DECODER THREAD

        fft_thread = threading.Thread(target=self.calculate_fft, name="FFT_THREAD")
        fft_thread.start()
        
        audio_thread_datac0 = threading.Thread(target=self.audio_datac0, name="AUDIO_THREAD DATAC0")
        audio_thread_datac0.start()

        audio_thread_datac1 = threading.Thread(target=self.audio_datac1, name="AUDIO_THREAD DATAC1")
        audio_thread_datac1.start()
        
        audio_thread_datac3 = threading.Thread(target=self.audio_datac3, name="AUDIO_THREAD DATAC3")
        audio_thread_datac3.start()
        
        hamlib_thread = threading.Thread(target=self.update_rig_data, name="HAMLIB_THREAD")
        hamlib_thread.start()
        
        worker_received = threading.Thread(target=self.worker_received, name="WORKER_THREAD")
        worker_received.start()
        
        worker_transmit = threading.Thread(target=self.worker_transmit, name="WORKER_THREAD")
        worker_transmit.start()
        
    # --------------------------------------------------------------------------------------------------------
    def audio_callback(self, data_in48k, frame_count, time_info, status):
        
        x = np.frombuffer(data_in48k, dtype=np.int16)
        x = self.resampler.resample48_to_8(x)    

        # avoid buffer overflow
        if not self.datac0_buffer.nbuffer+len(x) > self.datac0_buffer.size:
            self.datac0_buffer.push(x)
        # avoid buffer overflow    
        if not self.datac1_buffer.nbuffer+len(x) > self.datac1_buffer.size:
            self.datac1_buffer.push(x)
        # avoid buffer overflow
        if not self.datac3_buffer.nbuffer+len(x) > self.datac3_buffer.size:
            self.datac3_buffer.push(x)
        
        self.fft_data = bytes(x)
        
        if self.modoutqueue.empty():
            data_out48k = bytes(self.AUDIO_FRAMES_PER_BUFFER_TX*2)
        else:
            data_out48k = self.modoutqueue.get()
        
        return (data_out48k, pyaudio.paContinue)

    # --------------------------------------------------------------------------------------------------------


    def transmit(self, mode, repeats, repeat_delay, frames):     
        static.TRANSMITTING = True
        # open codec2 instance       
        #self.MODE = codec2.freedv_get_mode_value_by_name(mode)
        self.MODE = mode
        freedv = cast(codec2.api.freedv_open(self.MODE), c_void_p)

        # get number of bytes per frame for mode
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv)/8)
        payload_bytes_per_frame = bytes_per_frame -2

        # init buffer for data
        n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
        mod_out = create_string_buffer(n_tx_modem_samples * 2)

        # init buffer for preample
        n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(freedv)
        mod_out_preamble = create_string_buffer(n_tx_preamble_modem_samples * 2)

        # init buffer for postamble
        n_tx_postamble_modem_samples = codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
        mod_out_postamble = create_string_buffer(n_tx_postamble_modem_samples * 2)

        # add empty data to handle ptt toggle time
        data_delay_mseconds = 0 #miliseconds
        data_delay = int(self.MODEM_SAMPLE_RATE*(data_delay_mseconds/1000))
        mod_out_silence = create_string_buffer(data_delay*2)
        txbuffer = bytes(mod_out_silence) 

        for i in range(1,repeats+1):
            # write preamble to txbuffer
            codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
            #time.sleep(0.05)
            threading.Event().wait(0.05)
            txbuffer += bytes(mod_out_preamble)
                
            
            # create modulaton for n frames in list
            for n in range(0,len(frames)):

                # create buffer for data
                buffer = bytearray(payload_bytes_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
                buffer[:len(frames[n])] = frames[n] # set buffersize to length of data which will be send

                # create crc for data frame - we are using the crc function shipped with codec2 to avoid 
                # crc algorithm incompatibilities
                crc = ctypes.c_ushort(codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame))     # generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
                buffer += crc        # append crc16 to buffer   
                
                data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
                codec2.api.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and save it into mod_out pointer 
                #time.sleep(0.05)
                threading.Event().wait(0.05)
                txbuffer += bytes(mod_out)
                
            
            # append postamble to txbuffer          
            codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
            txbuffer += bytes(mod_out_postamble)
            #time.sleep(0.05)
            threading.Event().wait(0.05)
            # add delay to end of frames
            samples_delay = int(self.MODEM_SAMPLE_RATE*(repeat_delay/1000))
            mod_out_silence = create_string_buffer(samples_delay*2)
            txbuffer += bytes(mod_out_silence)
            #time.sleep(0.05)
            
            # resample up to 48k (resampler works on np.int16)
            x = np.frombuffer(txbuffer, dtype=np.int16)
            txbuffer_48k = self.resampler.resample8_to_48(x)

            # split modualted audio to chunks
            #https://newbedev.com/how-to-split-a-byte-string-into-separate-bytes-in-python
            txbuffer_48k = bytes(txbuffer_48k)
            chunk = [txbuffer_48k[i:i+self.AUDIO_FRAMES_PER_BUFFER_RX*2] for i in range(0, len(txbuffer_48k), self.AUDIO_FRAMES_PER_BUFFER_RX*2)]
            # add modulated chunks to fifo buffer
            for c in chunk:
                # if data is shorter than the expcected audio frames per buffer we need to append 0
                # to prevent the callback from stucking/crashing
                if len(c) < self.AUDIO_FRAMES_PER_BUFFER_RX*2:
                    delta = bytes(self.AUDIO_FRAMES_PER_BUFFER_RX*2 - len(c))
                    c += delta
                    structlog.get_logger("structlog").debug("[TNC] mod out shorter than audio buffer", delta=len(delta))
                self.modoutqueue.put(c)

        # maybe we need to toggle PTT before craeting modulation because of queue processing
        static.PTT_STATE = self.hamlib.set_ptt(True)
        while not self.modoutqueue.empty():
            pass
        static.PTT_STATE = self.hamlib.set_ptt(False)
      
        self.c_lib.freedv_close(freedv)
        self.modem_transmit_queue.task_done()
        static.TRANSMITTING = False
        threading.Event().set()

    def audio_datac0(self):             
        nbytes_datac0 = 0
        
        while self.audio_stream.is_active():
            threading.Event().wait(0.01)
            while self.datac0_buffer.nbuffer >= self.datac0_nin:        

                # demodulate audio
                nbytes_datac0 = codec2.api.freedv_rawdatarx(self.datac0_freedv, self.datac0_bytes_out, self.datac0_buffer.buffer.ctypes)
                self.datac0_buffer.pop(self.datac0_nin)
                self.datac0_nin = codec2.api.freedv_nin(self.datac0_freedv)
                if nbytes_datac0 == self.datac0_bytes_per_frame:
                    self.modem_received_queue.put([self.datac0_bytes_out, self.datac0_freedv ,self.datac0_bytes_per_frame])
                    self.get_scatter(self.datac0_freedv)
                    self.calculate_snr(self.datac0_freedv)

    def audio_datac1(self):
        nbytes_datac1 = 0
        while self.audio_stream.is_active():
            threading.Event().wait(0.01)
            while self.datac1_buffer.nbuffer >= self.datac1_nin:

                    # demodulate audio
                    nbytes_datac1 = codec2.api.freedv_rawdatarx(self.datac1_freedv, self.datac1_bytes_out, self.datac1_buffer.buffer.ctypes)
                    self.datac1_buffer.pop(self.datac1_nin)
                    self.datac1_nin = codec2.api.freedv_nin(self.datac1_freedv)
                    if nbytes_datac1 == self.datac1_bytes_per_frame:
                        self.modem_received_queue.put([self.datac1_bytes_out, self.datac1_freedv ,self.datac1_bytes_per_frame])
                        self.get_scatter(self.datac1_freedv)
                        self.calculate_snr(self.datac1_freedv)
                     
    def audio_datac3(self):                
            nbytes_datac3 = 0
            while self.audio_stream.is_active():
                threading.Event().wait(0.01)
                while self.datac3_buffer.nbuffer >= self.datac3_nin:

                    # demodulate audio    
                    nbytes_datac3 = codec2.api.freedv_rawdatarx(self.datac3_freedv, self.datac3_bytes_out, self.datac3_buffer.buffer.ctypes)
                    self.datac3_buffer.pop(self.datac3_nin)
                    self.datac3_nin = codec2.api.freedv_nin(self.datac3_freedv)
                    if nbytes_datac3 == self.datac3_bytes_per_frame:
                        self.modem_received_queue.put([self.datac3_bytes_out, self.datac3_freedv ,self.datac3_bytes_per_frame])
                        self.get_scatter(self.datac3_freedv)
                        self.calculate_snr(self.datac3_freedv)  
                              
                    
           
    # worker for FIFO queue for processing received frames           
    def worker_transmit(self):
        while True:
            data = self.modem_transmit_queue.get()
            self.transmit(mode=data[0], repeats=data[1], repeat_delay=data[2], frames=data[3])
            #self.modem_transmit_queue.task_done()            
            
                      
           
    # worker for FIFO queue for processing received frames           
    def worker_received(self):
        while True:
            data = self.modem_received_queue.get()
            # data[0] = bytes_out
            # data[1] = freedv session
            # data[2] = bytes_per_frame
            data_handler.DATA_QUEUE_RECEIVED.put([data[0], data[1], data[2]])
            self.modem_received_queue.task_done()
   

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

    
    def calculate_snr(self, freedv):

        modem_stats_snr = c_float()
        modem_stats_sync = c_int()

        self.c_lib.freedv_get_modem_stats(freedv, byref(
            modem_stats_sync), byref(modem_stats_snr))
        modem_stats_snr = modem_stats_snr.value

        try:
            static.SNR = round(modem_stats_snr, 1)
            return static.SNR
        except:
            static.SNR = 0
            return static.SNR

    def update_rig_data(self):
        while True:
            #time.sleep(0.5)
            threading.Event().wait(0.5)
            #(static.HAMLIB_FREQUENCY, static.HAMLIB_MODE, static.HAMLIB_BANDWITH, static.PTT_STATE) = self.hamlib.get_rig_data()
            static.HAMLIB_FREQUENCY = self.hamlib.get_frequency()
            static.HAMLIB_MODE = self.hamlib.get_mode()
            static.HAMLIB_BANDWITH = self.hamlib.get_bandwith()
    
    def calculate_fft(self):
        while True:
            #time.sleep(0.01)
            threading.Event().wait(0.01)
            # WE NEED TO OPTIMIZE THIS!
            if len(self.fft_data) >= 128:
            
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
                    
                    static.FFT = dfftlist[0:320] #200 --> bandwith 3000    

                except:
                    
                    structlog.get_logger("structlog").debug("[TNC] Setting fft=0")
                    # else 0
                    static.FFT = [0] * 320
            else:
                pass
                
    def set_frames_per_burst(self, n_frames_per_burst):
        codec2.api.freedv_set_frames_per_burst(self.datac1_freedv,n_frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.datac3_freedv,n_frames_per_burst)        
                
                
                
                
def get_bytes_per_frame(mode):
    freedv = cast(codec2.api.freedv_open(mode), c_void_p)

    # get number of bytes per frame for mode
    return int(codec2.api.freedv_get_bits_per_modem_frame(freedv)/8)
    
