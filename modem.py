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

import Hamlib



class RF():

    def __init__(self):
        
    
        # -------------------------------------------- LOAD FREEDV
        libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
        self.c_lib = ctypes.CDLL(libname)
        # --------------------------------------------CREATE PYAUDIO  INSTANCE
        self.p = pyaudio.PyAudio()
        # --------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE
        #static.AUDIO_SAMPLE_RATE_RX = int(self.p.get_device_info_by_index(static.AUDIO_INPUT_DEVICE)['defaultSampleRate'])
        #static.AUDIO_SAMPLE_RATE_TX = int(self.p.get_device_info_by_index(static.AUDIO_OUTPUT_DEVICE)['defaultSampleRate'])
        static.AUDIO_SAMPLE_RATE_TX = 48000
        static.AUDIO_SAMPLE_RATE_RX = 48000
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
        Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

        # Init RIG_MODEL_DUMMY
        self.my_rig = Hamlib.Rig(static.HAMLIB_DEVICE_ID)
        self.my_rig.set_conf("rig_pathname", static.HAMLIB_DEVICE_PORT)

        self.my_rig.set_conf("retry", "5")
        self.my_rig.set_conf("serial_speed", "19200")

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

        #self.my_rig.set_ptt(self.hamlib_ptt_type, 0)


        self.my_rig.open()


# --------------------------------------------------------------------------------------------------------
    def ptt_and_wait(self, state):
               
        if state:
            static.PTT_STATE = True
            self.my_rig.set_ptt(self.hamlib_ptt_type, 1)

            ptt_togle_timeout = time.time() + 0.1
            while time.time() < ptt_togle_timeout:
                pass

        else:
        
            ptt_togle_timeout = time.time() + 0.2
            while time.time() < ptt_togle_timeout:
                pass
                
            static.PTT_STATE = False
            self.my_rig.set_ptt(self.hamlib_ptt_type, 0)




    def play_audio(self):

        while True:
            time.sleep(0.01)
            #state_before_transmit = static.CHANNEL_STATE

            while len(self.streambuffer) > 0:
                time.sleep(0.01)
                if len(self.streambuffer) > 0:
                    self.audio_writing_to_stream = True
                    #print("es geht los...")
                    
                    #audio = audioop.ratecv(self.streambuffer,2,1,static.MODEM_SAMPLE_RATE, static.AUDIO_SAMPLE_RATE_TX, None)                                           
                    #self.stream_tx.write(audio[0])

                    self.streambuffer = bytes(self.streambuffer)
                    #print(type(self.streambuffer))
                    #print(self.streambuffer)
                    
                    # we need t wait a little bit until the buffer is filled. If we are not waiting, we are sending empty data
                    time.sleep(0.1)
                    self.stream_tx.write(self.streambuffer)
                    self.streambuffer = bytes()
            #static.CHANNEL_STATE = state_before_transmit
            self.audio_writing_to_stream = False
# --------------------------------------------------------------------------------------------------------

    def transmit_signalling(self, data_out):
        
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
                       
        # -------------- transmit audio
        #logging.debug("SENDING SIGNALLING FRAME " + str(data_out))

        state_before_transmit = static.CHANNEL_STATE
        static.CHANNEL_STATE = 'SENDING_SIGNALLING'
        
        self.ptt_and_wait(True)
        self.audio_writing_to_stream = True

        # wait until audio has been processed
        while self.audio_writing_to_stream:
            time.sleep(0.01)
            static.CHANNEL_STATE = 'SENDING_SIGNALLING'

        self.ptt_and_wait(False)                
        static.CHANNEL_STATE = state_before_transmit

        self.c_lib.freedv_close(freedv)

# --------------------------------------------------------------------------------------------------------
   # GET ARQ BURST FRAME VOM BUFFER AND MODULATE IT

    def transmit_arq_burst(self):
    
        # we could place this timing part inside the modem...
        # lets see if this is a good idea..
        static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp
        static.ARQ_START_OF_BURST = int(time.time()) # we need to update our timeout timestamp
    
        self.my_rig.set_ptt(self.hamlib_ptt_type, 1)

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
                static.ARQ_TX_N_TOTAL_ARQ_FRAMES = n_total_arq_frame.to_bytes(2, byteorder='big')

                arqframe = frame_type + \
                    bytes([static.ARQ_TX_N_FRAMES_PER_BURST]) + \
                    static.ARQ_TX_N_CURRENT_ARQ_FRAME + \
                    static.ARQ_TX_N_TOTAL_ARQ_FRAMES + \
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

                payload_data = bytes(static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + missing_frame - 1])

                n_current_arq_frame = static.ARQ_N_SENT_FRAMES + missing_frame
                static.ARQ_TX_N_CURRENT_ARQ_FRAME = n_current_arq_frame.to_bytes(2, byteorder='big')

                n_total_arq_frame = len(static.TX_BUFFER)
                static.ARQ_TX_N_TOTAL_ARQ_FRAMES = n_total_arq_frame.to_bytes(2, byteorder='big')

                arqframe = frame_type + \
                    bytes([static.ARQ_TX_N_FRAMES_PER_BURST]) + \
                    static.ARQ_TX_N_CURRENT_ARQ_FRAME + \
                    static.ARQ_TX_N_TOTAL_ARQ_FRAMES + \
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
        
        #print(len(self.streambuffer))                        

        # -------------- transmit audio
        
        self.ptt_and_wait(True)
        self.audio_writing_to_stream = True


        # wait until audio has been processed
        while self.audio_writing_to_stream:
            time.sleep(0.01)
            static.CHANNEL_STATE = 'SENDING_DATA'


        static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

        self.ptt_and_wait(False)

        self.c_lib.freedv_close(freedv)
# --------------------------------------------------------------------------------------------------------

    def receive(self, mode):
        force = False

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

            # stuck in sync counter
            stuck_in_sync_counter = 0
            stuck_in_sync_10_counter = 0
            #



            # here we do an unsync to be sure, the modem is in idle state and ready for new data
            # tests are showing, that this causes sync 10 triggers. So we should definitely not do this here!
            #self.c_lib.freedv_set_sync(freedv, 0)

            # here we do a buffer cleanup before returning to demod loop
            # tests are showing, that this causes sync 10 triggers. So we should definitely not do this here!
            #for i in range(0, 3):
            #    dummy_mod = bytes(self.c_lib.freedv_nin(freedv))
            #    self.c_lib.freedv_rawdatarx(freedv, bytes_out, dummy_mod)
            #    #self.stream_rx.read(10, exception_on_overflow=False)

            
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
                
                #data_in = audioop.mul(data_in, 2, 0.5)  
                #print(audioop.maxpp(data_in, 2))
                
                
                static.AUDIO_RMS = audioop.rms(data_in, 2)
                nbytes = self.c_lib.freedv_rawdatarx(freedv, bytes_out, data_in)  # demodulate audio
                ################print("listening-" + str(mode) + " - " + "nin: " + str(nin) + " - " + str(self.c_lib.freedv_get_rx_status(freedv)))


                # -------------STUCK IN SYNC DETECTOR
                stuck_in_sync_counter += 1
                if self.c_lib.freedv_get_rx_status(freedv) == 10:
                    stuck_in_sync_10_counter += 1
                    if mode != 14:
                        #self.c_lib.freedv_set_sync(freedv, 0)
                        logging.warning("MODEM | SYNC 10 TRIGGER | M:" + str(mode) + " | " + str(static.CHANNEL_STATE))

                if stuck_in_sync_counter == 33 and self.c_lib.freedv_get_rx_status(freedv) == 10:
                    logging.critical("MODEM | stuck in sync #1")
                    self.c_lib.freedv_set_sync(freedv, 0)  # FORCE UNSYNC
                    stuck_in_sync_counter = 0
                    stuck_in_sync_10_counter = 0

                elif stuck_in_sync_counter >= 66 and stuck_in_sync_10_counter >= 2:
                    logging.critical("MODEM | stuck in sync #2")
                    self.c_lib.freedv_set_sync(freedv, 0)  # FORCE UNSYNC
                    stuck_in_sync_counter = 0
                    stuck_in_sync_10_counter = 0
                # -----------------------------------

                self.calculate_snr(freedv)
                # forward data only if broadcast or we are the receiver
                # bytes_out[1:2] == callsign check for signalling frames, bytes_out[6:7] == callsign check for data frames, bytes_out[1:2] == b'\x01' --> broadcasts like CQ
                # we could also create an own function, which returns True. In this case we could add callsign blacklists and so on
                if nbytes == bytes_per_frame and bytes(bytes_out[1:2]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[6:7]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[1:2]) == b'\x01':
                    
                    self.calculate_ber(freedv)
                    self.calculate_snr(freedv)

                    # counter reset for stuck in sync counter
                    stuck_in_sync_counter = 0
                    stuck_in_sync_10_counter = 0
                    #

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
                        print("jahallo  alles erhalten")
     
                        bytes_out = (ctypes.c_ubyte * bytes_per_frame)
                        bytes_out = bytes_out()  # get pointer to bytes_out

     
                        #self.stream_rx.read(static.AUDIO_FRAMES_PER_BUFFER, exception_on_overflow=False)
                        
                        self.c_lib.freedv_set_sync(freedv, 0)  # FORCE UNSYNC
                        #for i in range(0, 3):
                        #    dummy_mod = bytes(self.c_lib.freedv_nin(freedv))
                        #    self.c_lib.freedv_rawdatarx(freedv, bytes_out, dummy_mod)
                            
                    # clear bytes_out buffer to be ready for next frames after successfull decoding

                    bytes_out = (ctypes.c_ubyte * bytes_per_frame)
                    bytes_out = bytes_out()  # get pointer to bytes_out

                    #if mode == 14:
                    #    bytes_out = (ctypes.c_ubyte * bytes_per_frame)
                    #    bytes_out = bytes_out()  # get pointer to bytes_out

                    #    self.c_lib.freedv_set_sync(freedv, 0)
                    #    self.stream_rx.read(static.AUDIO_FRAMES_PER_BUFFER, exception_on_overflow=False)
                        #for i in range(0, 3):
                        #    dummy_mod = bytes(self.c_lib.freedv_nin(freedv))
                        #    self.c_lib.freedv_rawdatarx(freedv, bytes_out, dummy_mod)
                else:
                    # for debugging purposes to receive all data
                    pass
                    # print(bytes_out[:-2])

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
            #static.SNR = int(modem_stats_snr)
            static.SNR = round(modem_stats_snr,1)
        except:
            static.SNR = 0
