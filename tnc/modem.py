#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import ctypes
from ctypes import *
import pathlib
import pyaudio
import audioop
import asyncio
#import sys
import logging
import time
import threading

import helpers
import static
import data_handler

import sys
sys.path.append("hamlib/linux")
import Hamlib

import numpy as np
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
        # --------------------------------------------OPEN AUDIO CHANNEL RX
        self.stream_rx = self.p.open(format=pyaudio.paInt16,
                                     channels=static.AUDIO_CHANNELS,
                                     rate=static.AUDIO_SAMPLE_RATE_RX,
                                     frames_per_buffer=static.AUDIO_FRAMES_PER_BUFFER,
                                     input=True,
                                     input_device_index=static.AUDIO_INPUT_DEVICE
                                     )
        # --------------------------------------------OPEN AUDIO CHANNEL TX
        self.stream_tx = self.p.open(format=pyaudio.paInt16,
                                     channels=1,
                                     rate=static.AUDIO_SAMPLE_RATE_TX,
                                     frames_per_buffer=static.AUDIO_FRAMES_PER_BUFFER,  # n_nom_modem_samples
                                     output=True,
                                     output_device_index=static.AUDIO_OUTPUT_DEVICE,  # static.AUDIO_OUTPUT_DEVICE
                                     )

        self.streambuffer = bytes(0)
        self.audio_writing_to_stream = False
        # --------------------------------------------START DECODER THREAD
        FREEDV_DECODER_THREAD_10 = threading.Thread(target=self.receive, args=[10], name="FREEDV_DECODER_THREAD_10")
        FREEDV_DECODER_THREAD_10.start()

        #FREEDV_DECODER_THREAD_11 = threading.Thread(target=self.receive, args=[11], name="FREEDV_DECODER_THREAD_11")
        #FREEDV_DECODER_THREAD_11.start()

        FREEDV_DECODER_THREAD_12 = threading.Thread(target=self.receive, args=[12], name="FREEDV_DECODER_THREAD_12")
        FREEDV_DECODER_THREAD_12.start()

        FREEDV_DECODER_THREAD_14 = threading.Thread(target=self.receive, args=[static.FREEDV_SIGNALLING_MODE], name="FREEDV_DECODER_THREAD_14")
        FREEDV_DECODER_THREAD_14.start()

        FREEDV_PLAYBACK_THREAD = threading.Thread(target=self.play_audio, name="FREEDV_DECODER_THREAD_14")
        FREEDV_PLAYBACK_THREAD.start()

        # --------------------------------------------CONFIGURE HAMLIB


        # try to init hamlib
        try:
            
            Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)
            
            self.my_rig = Hamlib.Rig(static.HAMLIB_DEVICE_ID)
            self.my_rig.set_conf("rig_pathname", static.HAMLIB_DEVICE_PORT)

            self.my_rig.set_conf("retry", "5")
            self.my_rig.set_conf("serial_speed", static.HAMLIB_SERIAL_SPEED)

        #self.my_rig.set_conf("dtr_state", "OFF")
        #my_rig.set_conf("rts_state", "OFF")
        #self.my_rig.set_conf("ptt_type", "RTS")
        #my_rig.set_conf("ptt_type", "RIG_PTT_SERIAL_RTS")
    
            self.my_rig.set_conf("serial_handshake", "None")
            self.my_rig.set_conf("stop_bits", "1")
            self.my_rig.set_conf("data_bits", "8")
           
        #my_rig.set_ptt(Hamlib.RIG_PTT_RIG,0)
        #my_rig.set_ptt(Hamlib.RIG_PTT_SERIAL_DTR,0)
        #my_rig.set_ptt(Hamlib.RIG_PTT_SERIAL_RTS,1)    

            if static.HAMLIB_PTT_TYPE == 'RIG_PTT_RIG':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_RIG
            
            elif static.HAMLIB_PTT_TYPE == 'RIG_PTT_SERIAL_DTR':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_DTR
            
            elif static.HAMLIB_PTT_TYPE == 'RTS':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_RTS
                self.my_rig.set_conf("dtr_state", "OFF")
                self.my_rig.set_conf("ptt_type", "RTS")      
                  
            elif static.HAMLIB_PTT_TYPE == 'RIG_PTT_PARALLEL':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_PARALLEL
            
            elif static.HAMLIB_PTT_TYPE == 'RIG_PTT_RIG_MICDATA':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_RIG_MICDATA
            
            elif static.HAMLIB_PTT_TYPE == 'RIG_PTT_CM108':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_CM108
            
            else:  # static.HAMLIB_PTT_TYPE == 'RIG_PTT_NONE':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_NONE


            self.my_rig.open()
            
            # set rig mode to USB
            self.my_rig.set_mode(Hamlib.RIG_MODE_USB)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("can't open rig")

    
# --------------------------------------------------------------------------------------------------------
    def ptt_and_wait(self, state):
        static.PTT_STATE = state
                       
        if state:

            self.my_rig.set_ptt(self.hamlib_ptt_type, 1)
            #rigctld.ptt_enable()
            ptt_toggle_timeout = time.time() + 0.5
            while time.time() < ptt_toggle_timeout:
                pass
                      

        else:
        
            ptt_toggle_timeout = time.time() + 0.5
            while time.time() < ptt_toggle_timeout:
                pass
                
            self.my_rig.set_ptt(self.hamlib_ptt_type, 0)
            #rigctld.ptt_disable()
                        
        return False


    def play_audio(self):

        while True:
            time.sleep(0.01)

            #while len(self.streambuffer) > 0:
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
        #print(static.CHANNEL_STATE)
                
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(static.FREEDV_SIGNALLING_MODE)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_per_frame = bytes_per_frame - 2
        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)  # get n_tx_modem_samples which defines the size of the modulation object
        n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(freedv)
        n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(freedv)
        
        mod_out = ctypes.c_short * n_tx_modem_samples
        mod_out = mod_out()
        
        mod_out_preamble = ctypes.c_short * n_tx_preamble_modem_samples  # *2 #1760 for mode 10,11,12 #4000 for mode 9
        mod_out_preamble = mod_out_preamble()

        mod_out_postamble = ctypes.c_short * n_tx_postamble_modem_samples  # *2 #1760 for mode 10,11,12 #4000 for mode 9
        mod_out_postamble = mod_out_postamble()

        buffer = bytearray(payload_per_frame)  # use this if CRC16 checksum is required ( DATA1-3)
        buffer[:len(data_out)] = data_out  # set buffersize to length of data which will be send

        crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
        crc = crc.value.to_bytes(2, byteorder='big')  # convert crc to 2 byte hex string
        buffer += crc        # append crc16 to buffer
        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)

        self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        self.c_lib.freedv_rawdatatx(freedv, mod_out, data)  # modulate DATA and safe it into mod_out pointer
        self.c_lib.freedv_rawdatapostambletx(freedv, mod_out_postamble)

        self.streambuffer = bytearray()
        self.streambuffer += bytes(mod_out_preamble)
        self.streambuffer += bytes(mod_out)
        self.streambuffer += bytes(mod_out_postamble)
        
        converted_audio = audioop.ratecv(self.streambuffer,2,1,static.MODEM_SAMPLE_RATE, static.AUDIO_SAMPLE_RATE_TX, None)
        self.streambuffer = bytes(converted_audio[0])
        # append frame again with as much as in count defined
        for i in range(1, count):
            self.streambuffer += bytes(converted_audio[0])
            #print(len(self.streambuffer))
        #self.streambuffer += bytes(converted_audio[0])
        #print(len(self.streambuffer))                       
        
        # -------------- transmit audio
        #logging.debug("SENDING SIGNALLING FRAME " + str(data_out))

        ##state_before_transmit = static.CHANNEL_STATE
        ##static.CHANNEL_STATE = 'SENDING_SIGNALLING'
        
        while self.ptt_and_wait(True):
            pass
        self.audio_writing_to_stream = True
        
        # wait until audio has been processed
        while self.audio_writing_to_stream:
            time.sleep(0.01)
            static.CHANNEL_STATE = 'SENDING_SIGNALLING'

        self.ptt_and_wait(False)                
        ## we have a problem with the receiving state
        ##static.CHANNEL_STATE = state_before_transmit
        if state_before_transmit != 'RECEIVING_DATA':
            static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'
        else:
            static.CHANNEL_STATE = state_before_transmit
            
        self.c_lib.freedv_close(freedv)

# --------------------------------------------------------------------------------------------------------
   # GET ARQ BURST FRAME VOM BUFFER AND MODULATE IT

    def transmit_arq_burst(self):
    
        # we could place this timing part inside the modem...
        # lets see if this is a good idea..
        static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp
        static.ARQ_START_OF_BURST = int(time.time()) # we need to update our timeout timestamp
        
        state_before_transmit = static.CHANNEL_STATE
        static.CHANNEL_STATE = 'SENDING_DATA'

        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(static.ARQ_DATA_CHANNEL_MODE)

        static.FREEDV_DATA_BYTES_PER_FRAME = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv) / 8)
        static.FREEDV_DATA_PAYLOAD_PER_FRAME = static.FREEDV_DATA_BYTES_PER_FRAME - 2

        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)  # *2 #get n_tx_modem_samples which defines the size of the modulation object
        n_tx_preamble_modem_samples = self.c_lib.freedv_get_n_tx_preamble_modem_samples(freedv)
        n_tx_postamble_modem_samples = self.c_lib.freedv_get_n_tx_postamble_modem_samples(freedv)
        
        mod_out = ctypes.c_short * n_tx_modem_samples
        mod_out = mod_out()
        
        mod_out_preamble = ctypes.c_short * n_tx_preamble_modem_samples  # *2 #1760 for mode 10,11,12 #4000 for mode 9
        mod_out_preamble = mod_out_preamble()

        mod_out_postamble = ctypes.c_short * n_tx_postamble_modem_samples  # *2 #1760 for mode 10,11,12 #4000 for mode 9
        mod_out_postamble = mod_out_postamble()
        
        self.streambuffer = bytearray()
        self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        self.streambuffer += bytes(mod_out_preamble)
        
        if not static.ARQ_RPT_RECEIVED:
               
            for n in range(0, static.ARQ_TX_N_FRAMES_PER_BURST):
                # ---------------------------BUILD ARQ BURST ---------------------------------------------------------------------
                frame_type = 10 + n + 1  # static.ARQ_TX_N_FRAMES_PER_BURST
                frame_type = bytes([frame_type])

                payload_data = bytes(static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + n])

                n_current_arq_frame = static.ARQ_N_SENT_FRAMES + n + 1
                static.ARQ_TX_N_CURRENT_ARQ_FRAME = n_current_arq_frame.to_bytes(2, byteorder='big')

                n_total_arq_frame = len(static.TX_BUFFER)
                #static.ARQ_TX_N_TOTAL_ARQ_FRAMES = n_total_arq_frame

                arqframe = frame_type + \
                    bytes([static.ARQ_TX_N_FRAMES_PER_BURST]) + \
                    static.ARQ_TX_N_CURRENT_ARQ_FRAME + \
                    n_total_arq_frame.to_bytes(2, byteorder='big') + \
                    static.DXCALLSIGN_CRC8 + \
                    static.MYCALLSIGN_CRC8 + \
                    payload_data

                buffer = bytearray(static.FREEDV_DATA_PAYLOAD_PER_FRAME)  # create TX buffer
                buffer[:len(arqframe)] = arqframe  # set buffersize to length of data which will be send

                crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), static.FREEDV_DATA_PAYLOAD_PER_FRAME))     # generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big')  # convert crc to 2 byte hex string
                buffer += crc        # append crc16 to buffer

                data = (ctypes.c_ubyte * static.FREEDV_DATA_BYTES_PER_FRAME).from_buffer_copy(buffer)
                
                self.c_lib.freedv_rawdatatx(freedv, mod_out, data)  # modulate DATA and safe it into mod_out pointer
                self.streambuffer += bytes(mod_out)
               

        elif static.ARQ_RPT_RECEIVED:

            for n in range(0, len(static.ARQ_RPT_FRAMES)):
                missing_frame = int.from_bytes(static.ARQ_RPT_FRAMES[n], "big")

            # ---------------------------BUILD ARQ BURST ---------------------------------------------------------------------
                frame_type = 10 + missing_frame  # static.ARQ_TX_N_FRAMES_PER_BURST
                frame_type = bytes([frame_type])

                try:
                    payload_data = bytes(static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + missing_frame - 1])
                except:
                    print("modem buffer selection problem with ARQ RPT frames")
                    
                n_current_arq_frame = static.ARQ_N_SENT_FRAMES + missing_frame
                static.ARQ_TX_N_CURRENT_ARQ_FRAME = n_current_arq_frame.to_bytes(2, byteorder='big')

                n_total_arq_frame = len(static.TX_BUFFER)
                #static.ARQ_TX_N_TOTAL_ARQ_FRAMES = n_total_arq_frame

                arqframe = frame_type + \
                    bytes([static.ARQ_TX_N_FRAMES_PER_BURST]) + \
                    static.ARQ_TX_N_CURRENT_ARQ_FRAME + \
                    n_total_arq_frame.to_bytes(2, byteorder='big') + \
                    static.DXCALLSIGN_CRC8 + \
                    static.MYCALLSIGN_CRC8 + \
                    payload_data

                buffer = bytearray(static.FREEDV_DATA_PAYLOAD_PER_FRAME)  # create TX buffer
                buffer[:len(arqframe)] = arqframe  # set buffersize to length of data which will be send

                crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), static.FREEDV_DATA_PAYLOAD_PER_FRAME))     # generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big')  # convert crc to 2 byte hex string
                buffer += crc        # append crc16 to buffer

                data = (ctypes.c_ubyte * static.FREEDV_DATA_BYTES_PER_FRAME).from_buffer_copy(buffer)
                
                self.c_lib.freedv_rawdatatx(freedv, mod_out, data)  # modulate DATA and safe it into mod_out pointer              
                self.streambuffer += bytes(mod_out)

                       
        self.c_lib.freedv_rawdatapostambletx(freedv, mod_out_postamble)
        self.streambuffer += bytes(mod_out_postamble)
        
        converted_audio = audioop.ratecv(self.streambuffer,2,1,static.MODEM_SAMPLE_RATE, static.AUDIO_SAMPLE_RATE_TX, None)
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
# --------------------------------------------------------------------------------------------------------

    def receive(self, mode):
        force = False

        # create new codec2 instance
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(mode)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv) / 8)

        if mode == static.FREEDV_SIGNALLING_MODE:
            static.FREEDV_SIGNALLING_BYTES_PER_FRAME = bytes_per_frame
            static.FREEDV_SIGNALLING_PAYLOAD_PER_FRAME = bytes_per_frame - 2

            self.c_lib.freedv_set_frames_per_burst(freedv, 1)

        elif mode == static.ARQ_DATA_CHANNEL_MODE:
            static.FREEDV_DATA_BYTES_PER_FRAME = bytes_per_frame
            static.FREEDV_DATA_PAYLOAD_PER_FRAME = bytes_per_frame - 2

            self.c_lib.freedv_set_frames_per_burst(freedv, 0)
        else:
            #pass
            self.c_lib.freedv_set_frames_per_burst(freedv, 0)

        bytes_out = (ctypes.c_ubyte * bytes_per_frame)
        bytes_out = bytes_out()  # get pointer to bytes_out

        while static.FREEDV_RECEIVE == True:
            time.sleep(0.01)
            
            # lets get the frequency, mode and bandwith
            self.get_radio_stats()
            
            # lets get scatter data
            self.get_scatter(freedv)
            
            # demod loop         
            while (static.CHANNEL_STATE == 'RECEIVING_DATA' and static.ARQ_DATA_CHANNEL_MODE == mode) or (static.CHANNEL_STATE == 'RECEIVING_SIGNALLING' and static.FREEDV_SIGNALLING_MODE == mode):
                time.sleep(0.01)

                # refresh vars, so the correct parameters of the used mode are set
                if mode == static.ARQ_DATA_CHANNEL_MODE:
                    static.FREEDV_DATA_BYTES_PER_FRAME = bytes_per_frame
                    static.FREEDV_DATA_PAYLOAD_PER_FRAME = bytes_per_frame - 2

                nin = self.c_lib.freedv_nin(freedv)
                nin = int(nin*(static.AUDIO_SAMPLE_RATE_RX/static.MODEM_SAMPLE_RATE))
                
                data_in = self.stream_rx.read(nin, exception_on_overflow=False)
                                              
                data_in = audioop.ratecv(data_in,2,1,static.AUDIO_SAMPLE_RATE_RX, static.MODEM_SAMPLE_RATE, None) 
                data_in = data_in[0]
                
                self.calculate_fft(data_in)
                
                                
                static.AUDIO_RMS = audioop.rms(data_in, 2)
                nbytes = self.c_lib.freedv_rawdatarx(freedv, bytes_out, data_in)  # demodulate audio
                #print("listening-" + str(mode) + " - " + "nin: " + str(nin) + " - " + str(self.c_lib.freedv_get_rx_status(freedv)))

                
                # get scatter data and snr data
                self.get_scatter(freedv)
                self.calculate_snr(freedv)
                
                # forward data only if broadcast or we are the receiver
                # bytes_out[1:2] == callsign check for signalling frames, bytes_out[6:7] == callsign check for data frames, bytes_out[1:2] == b'\x01' --> broadcasts like CQ
                # we could also create an own function, which returns True. In this case we could add callsign blacklists and so on
                if nbytes == bytes_per_frame and bytes(bytes_out[1:2]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[6:7]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[1:2]) == b'\x01':
                    
                    self.calculate_snr(freedv)
                    #static.SCATTER = []

                    # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
                    frametype = int.from_bytes(bytes(bytes_out[:1]), "big")
                    frame = frametype - 10
                    n_frames_per_burst = int.from_bytes(bytes(bytes_out[1:2]), "big")

                    #self.c_lib.freedv_set_frames_per_burst(freedv_data, n_frames_per_burst);

                    if 50 >= frametype >= 10:
                        if frame != 3 or force == True:

                            data_handler.arq_data_received(bytes(bytes_out[:-2]))  # send payload data to arq checker without CRC16

                            #print("static.ARQ_RX_BURST_BUFFER.count(None) " + str(static.ARQ_RX_BURST_BUFFER.count(None)))
                            if static.ARQ_RX_BURST_BUFFER.count(None) <= 1:
                                logging.debug("FULL BURST BUFFER ---> UNSYNC")
                                self.c_lib.freedv_set_sync(freedv, 0)

                        else:
                            logging.critical("---------------------------SIMULATED MISSING FRAME")
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

                    # FRAME NAK
                    elif frametype == 63:
                        logging.debug("FRAME NAK RECEIVED....")
                        data_handler.frame_nack_received(bytes_out[:-2])
                        
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

                    # ARQ CONNECT
                    elif frametype == 220:
                        logging.info("ARQ CONNECT RECEIVED....")
                        data_handler.arq_received_connect(bytes_out[:-2])

                    # ARQ CONNECT ACK / KEEP ALIVE
                    elif frametype == 221:
                        logging.info("ARQ CONNECT ACK RECEIVED / KEEP ALIVE....")
                        data_handler.arq_received_connect_keep_alive(bytes_out[:-2])

                    # ARQ CONNECT ACK / KEEP ALIVE
                    elif frametype == 222:
                        logging.debug("ARQ DISCONNECT RECEIVED")
                        data_handler.arq_disconnect_received(bytes_out[:-2])

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

                    # DO UNSYNC AFTER LAST BURST by checking the frame nums agains the total frames per burst
                    if frame == n_frames_per_burst:
                        logging.debug("LAST FRAME ---> UNSYNC")
     
                        bytes_out = (ctypes.c_ubyte * bytes_per_frame)
                        bytes_out = bytes_out()  # get pointer to bytes_out

                        self.c_lib.freedv_set_sync(freedv, 0)  # FORCE UNSYNC
 
                    # clear bytes_out buffer to be ready for next frames after successfull decoding

                    bytes_out = (ctypes.c_ubyte * bytes_per_frame)
                    bytes_out = bytes_out()  # get pointer to bytes_out

                else:
                    # for debugging purposes to receive all data
                    pass
                    # print(bytes_out[:-2])
    def get_scatter(self, freedv):
        modemStats = MODEMSTATS()
        self.c_lib.freedv_get_modem_extended_stats.restype = None
        self.c_lib.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats))
        

        scatterdata = []
        for i in range(MODEM_STATS_NC_MAX):
            for j in range(MODEM_STATS_NR_MAX):    
                #check if odd or not to get every 2nd item for x
                if (j % 2) == 0: 
                    xsymbols = modemStats.rx_symbols[i][j]
                    ysymbols = modemStats.rx_symbols[i][j+1]   
                    # check if value 0.0 or has real data
                    if xsymbols != 0.0 and ysymbols != 0.0:
                        scatterdata.append({"x" : xsymbols, "y" : ysymbols })
        
        # only append scatter data if new data arrived
        if len(scatterdata) > 0:
            static.SCATTER = scatterdata   
        
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
        
        self.c_lib.freedv_get_modem_stats(freedv,byref(modem_stats_sync), byref(modem_stats_snr))
        modem_stats_snr = modem_stats_snr.value
        try:
            static.SNR = round(modem_stats_snr,1)
        except:
            static.SNR = 0
            
    def get_radio_stats(self):
        static.HAMLIB_FREQUENCY = int(self.my_rig.get_freq())
        (hamlib_mode, static.HAMLIB_BANDWITH) = self.my_rig.get_mode()
        static.HAMLIB_MODE = Hamlib.rig_strrmode(hamlib_mode)
        #static.HAMLIB_FREQUENCY = rigctld.get_frequency()
        #static.HAMLIB_MODE = rigctld.get_mode()[0]
        #static.HAMLIB_BANDWITH = rigctld.get_mode()[1]
        
                            
    def calculate_fft(self, data_in):
        # WE NEED TO OPTIMIZE THIS!
        
        
        # https://gist.github.com/ZWMiller/53232427efc5088007cab6feee7c6e4c
        audio_data = np.fromstring(data_in, np.int16)
        # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
        # and make sure it's not imaginary

        try:
            fftarray = np.fft.rfft(audio_data)
            # set value 0 to 1 to avoid division by zero 
            fftarray[fftarray == 0] = 1
            dfft = 10.*np.log10(abs(fftarray))
            dfftlist = dfft.tolist()
                
            # send fft only if receiving
            if static.CHANNEL_STATE == 'RECEIVING_SIGNALLING' or static.CHANNEL_STATE == 'RECEIVING_DATA':
                static.FFT = dfftlist[20:380]
        except:
            print("setting fft = 0")
            # else 0
            static.FFT = [0] * 400
        
