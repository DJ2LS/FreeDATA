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


class RF():

    def __init__(self):
        self.AUDIO_SAMPLE_RATE_RX = 48000
        self.AUDIO_SAMPLE_RATE_TX = 48000
        self.MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
        self.AUDIO_FRAMES_PER_BUFFER_RX = 2400*2  #8192
        self.AUDIO_FRAMES_PER_BUFFER_TX = 2400     #8192 Lets to some tests with very small chunks for TX
        self.AUDIO_CHUNKS = 48 #8 * (self.AUDIO_SAMPLE_RATE_RX/self.MODEM_SAMPLE_RATE) #48
        self.AUDIO_CHANNELS = 1
        
        # make sure our resampler will work
        assert (self.AUDIO_SAMPLE_RATE_RX / self.MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48
        
        # small hack for initializing codec2 via codec2.py module
        # TODO: we need to change the entire modem module to integrate codec2 module
        self.c_lib = codec2.api
        self.resampler = codec2.resampler()

        # init FIFO queue to store received frames in
        self.dataqueue = queue.Queue()

        # init FIFO queue to store modulation out in
        self.modoutqueue = queue.Queue()
        
        
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


        
        # --------------------------------------------START DECODER THREAD

        AUDIO_THREAD = threading.Thread(target=self.audio, name="AUDIO_THREAD")
        AUDIO_THREAD.start()

        HAMLIB_THREAD = threading.Thread(target=self.update_rig_data, name="HAMLIB_THREAD")
        HAMLIB_THREAD.start()
        
        WORKER_THREAD = threading.Thread(target=self.worker, name="WORKER_THREAD")
        WORKER_THREAD.start()

        self.fft_data = bytes()
        FFT_THREAD = threading.Thread(target=self.calculate_fft, name="FFT_THREAD")
        FFT_THREAD.start()

        
        # --------------------------------------------INIT AND OPEN HAMLIB
        self.hamlib = rig.radio()
        self.hamlib.open_rig(devicename=static.HAMLIB_DEVICE_NAME, deviceport=static.HAMLIB_DEVICE_PORT, hamlib_ptt_type='RIG', serialspeed=9600)

    # --------------------------------------------------------------------------------------------------------
    def audio_callback(self, data_in48k, frame_count, time_info, status):
        
        x = np.frombuffer(data_in48k, dtype=np.int16)
        x = self.resampler.resample48_to_8(x)    

        self.datac0_buffer.push(x)
        self.datac1_buffer.push(x)
        self.datac3_buffer.push(x)
    
        # refill fft_data buffer so we can plot a fft
        if len(self.fft_data) < 1024:
            self.fft_data += bytes(x)

        
        if self.modoutqueue.empty():
            data_out48k = bytes(self.AUDIO_FRAMES_PER_BUFFER_TX*2*2)
        else:
            data_out48k = self.modoutqueue.get()
        
        return (data_out48k, pyaudio.paContinue)

    # --------------------------------------------------------------------------------------------------------


    def transmit(self, mode, repeats, repeat_delay, frames):
        #print(mode)
        #mode = codec2.freedv_get_mode_value_by_name(mode)
        #print(mode)
        
        #state_before_transmit = static.CHANNEL_STATE
        #static.CHANNEL_STATE = 'SENDING_SIGNALLING'
        
        
        
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
        data_delay_seconds = 250
        data_delay = int(self.MODEM_SAMPLE_RATE*(data_delay_seconds/1000))
        mod_out_silence = create_string_buffer(data_delay*2)
        txbuffer = bytes(mod_out_silence) 

        for i in range(1,repeats+1):
            
            # write preamble to txbuffer
            codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
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

                txbuffer += bytes(mod_out)
                
            
            # append postamble to txbuffer          
            codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
            txbuffer += bytes(mod_out_postamble)

            # add delay to end of frames
            samples_delay = int(self.MODEM_SAMPLE_RATE*(repeat_delay/1000))
            mod_out_silence = create_string_buffer(samples_delay*2)
            txbuffer += bytes(mod_out_silence)
            
            
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
                    c += bytes(self.AUDIO_FRAMES_PER_BUFFER_RX*2 - len(c))
                self.modoutqueue.put(c)

        # maybe we need to toggle PTT before craeting modulation because of queue processing
        static.PTT_STATE = self.hamlib.set_ptt(True)
        while not self.modoutqueue.empty():
            pass
        static.PTT_STATE = self.hamlib.set_ptt(False)
        
      
        self.c_lib.freedv_close(freedv)        
        return True



    '''
    def transmit_signalling(self, data_out, count):
        state_before_transmit = static.CHANNEL_STATE
        static.CHANNEL_STATE = 'SENDING_SIGNALLING'

        mod_out = create_string_buffer(self.datac0_n_tx_modem_samples * 2)
        mod_out_preamble = create_string_buffer(self.datac0_n_tx_preamble_modem_samples * 2)
        mod_out_postamble = create_string_buffer(self.datac0_n_tx_postamble_modem_samples * 2)

        buffer = bytearray(self.datac0_payload_per_frame)
        # set buffersize to length of data which will be send
        buffer[:len(data_out)] = data_out

        crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), self.datac0_payload_per_frame))     # generate CRC16
        # convert crc to 2 byte hex string
        crc = crc.value.to_bytes(2, byteorder='big')
        buffer += crc        # append crc16 to buffer
        data = (ctypes.c_ubyte * self.datac0_bytes_per_frame).from_buffer_copy(buffer)
        
        # modulate DATA and safe it into mod_out pointer
        self.c_lib.freedv_rawdatapreambletx(self.datac0_freedv, mod_out_preamble)
        self.c_lib.freedv_rawdatatx(self.datac0_freedv, mod_out, data)
        self.c_lib.freedv_rawdatapostambletx(self.datac0_freedv, mod_out_postamble)

        self.streambuffer = bytearray()
        self.streambuffer += bytes(mod_out_preamble)
        self.streambuffer += bytes(mod_out)
        self.streambuffer += bytes(mod_out_postamble)

        # resample up to 48k (resampler works on np.int16)
        x = np.frombuffer(self.streambuffer, dtype=np.int16)
        txbuffer_48k = self.resampler.resample8_to_48(x)
        
        
        # append frame again with as much as in count defined
        #for i in range(1, count):
        #    self.streambuffer += bytes(txbuffer_48k.tobytes())

        while self.ptt_and_wait(True):
            pass
        
        # set channel state   
        static.CHANNEL_STATE = 'SENDING_SIGNALLING'       
            
        # start writing audio data to audio stream  
        #self.stream_tx.write(self.streambuffer)
        self.stream_tx.write(txbuffer_48k.tobytes())


        # set ptt back to false
        self.ptt_and_wait(False)
        
        
        # we have a problem with the receiving state
        if state_before_transmit != 'RECEIVING_DATA':
            static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'
        else:
            static.CHANNEL_STATE = state_before_transmit
        
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

        # resample up to 48k (resampler works on np.int16)
        x = np.frombuffer(self.streambuffer, dtype=np.int16)
        txbuffer_48k = self.resampler.resample8_to_48(x)

        # -------------- transmit audio

        while self.ptt_and_wait(True):
            pass

        # set channel state
        static.CHANNEL_STATE = 'SENDING_DATA'
        
        # write audio to stream
        self.stream_tx.write(txbuffer_48k.tobytes())
        
        static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

        self.ptt_and_wait(False)

        # close codec2 instance
        self.c_lib.freedv_close(freedv)
        
        return True
# --------------------------------------------------------------------------------------------------------
    '''
    def audio(self):
        try:                        
            print(f"starting pyaudio callback", file=sys.stderr)
            self.audio_stream.start_stream()
        except Exception as e:
            print(f"pyAudio error: {e}", file=sys.stderr) 
           

        while self.audio_stream.is_active():
            while self.datac0_buffer.nbuffer >= self.datac0_nin:        
                # demodulate audio
                nbytes = codec2.api.freedv_rawdatarx(self.datac0_freedv, self.datac0_bytes_out, self.datac0_buffer.buffer.ctypes)
                self.datac0_buffer.pop(self.datac0_nin)
                self.datac0_nin = codec2.api.freedv_nin(self.datac0_freedv)
                if nbytes == self.datac0_bytes_per_frame:
                    self.dataqueue.put([self.datac0_bytes_out, self.datac0_freedv ,self.datac0_bytes_per_frame])
                    self.get_scatter(self.datac0_freedv)
                    self.calculate_snr(self.datac0_freedv)
                        
            while self.datac1_buffer.nbuffer >= self.datac1_nin:
                # demodulate audio
                nbytes = codec2.api.freedv_rawdatarx(self.datac1_freedv, self.datac1_bytes_out, self.datac1_buffer.buffer.ctypes)
                self.datac1_buffer.pop(self.datac1_nin)
                self.datac1_nin = codec2.api.freedv_nin(self.datac1_freedv)
                if nbytes == self.datac1_bytes_per_frame:
                    self.dataqueue.put([self.datac1_bytes_out, self.datac1_freedv ,self.datac1_bytes_per_frame])
                    self.get_scatter(self.datac1_freedv)
                    self.calculate_snr(self.datac1_freedv)
                                            
            while self.datac3_buffer.nbuffer >= self.datac3_nin:
                # demodulate audio    
                nbytes = codec2.api.freedv_rawdatarx(self.datac3_freedv, self.datac3_bytes_out, self.datac3_buffer.buffer.ctypes)
                self.datac3_buffer.pop(self.datac3_nin)
                self.datac3_nin = codec2.api.freedv_nin(self.datac3_freedv)
                if nbytes == self.datac3_bytes_per_frame:
                    self.dataqueue.put([self.datac3_bytes_out, self.datac3_freedv ,self.datac3_bytes_per_frame])
                    self.get_scatter(self.datac3_freedv)
                    self.calculate_snr(self.datac3_freedv)            
            
            
            
                      
           
    # worker for FIFO queue for processing received frames           
    def worker(self):
        while True:
            time.sleep(0.01)
            data = self.dataqueue.get()
            self.process_data(data[0], data[1], data[2])
            self.dataqueue.task_done()
   
    
    # forward data only if broadcast or we are the receiver
    # bytes_out[1:2] == callsign check for signalling frames, 
    # bytes_out[6:7] == callsign check for data frames, 
    # bytes_out[1:2] == b'\x01' --> broadcasts like CQ with n frames per_burst = 1
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

                # send payload data to arq checker without CRC16
                data_handler.arq_data_received(bytes(bytes_out[:-2]), bytes_per_frame)

                #print("static.ARQ_RX_BURST_BUFFER.count(None) " + str(static.ARQ_RX_BURST_BUFFER.count(None)))
                if static.RX_BURST_BUFFER.count(None) <= 1:
                    logging.debug("FULL BURST BUFFER ---> UNSYNC")
                    self.c_lib.freedv_set_sync(freedv, 0)


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
                logging.debug("ARQ arq_received_data_channel_opener")
                data_handler.arq_received_data_channel_opener(bytes_out[:-2])

            # ARQ CHANNEL IS OPENED
            elif frametype == 226:
                logging.debug("ARQ arq_received_channel_is_open")
                data_handler.arq_received_channel_is_open(bytes_out[:-2])

            # ARQ CONNECT ACK / KEEP ALIVE
            elif frametype == 230:
                logging.debug("BEACON RECEIVED")
                data_handler.received_beacon(bytes_out[:-2])

            elif frametype == 255:
                structlog.get_logger("structlog").debug("TESTFRAME RECEIVED", frame=bytes_out[:])
                
                
            else:
                structlog.get_logger("structlog").warning("[TNC] ARQ - other frame type", frametype=frametype)

            '''
            # DO UNSYNC AFTER LAST BURST by checking the frame nums against the total frames per burst
            if frame == n_frames_per_burst:
                logging.info("LAST FRAME ---> UNSYNC")
                self.c_lib.freedv_set_sync(freedv, 0)  # FORCE UNSYNC
            '''

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
            
    '''        
    def calculate_ber(self, freedv):
        Tbits = self.c_lib.freedv_get_total_bits(freedv)
        Terrs = self.c_lib.freedv_get_total_bit_errors(freedv)

        if Tbits != 0:
            ber = (Terrs / Tbits) * 100
            static.BER = int(ber)

        self.c_lib.freedv_set_total_bit_errors(freedv, 0)
        self.c_lib.freedv_set_total_bits(freedv, 0)
    '''
    
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


    def update_rig_data(self):
        while True:
            time.sleep(0.1)            
            (static.HAMLIB_FREQUENCY, static.HAMLIB_MODE, static.HAMLIB_BANDWITH, static.PTT_STATE) = self.hamlib.get_rig_data()

    
    
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
