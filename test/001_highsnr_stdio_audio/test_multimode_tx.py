#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ctypes
from ctypes import *
import pathlib
import pyaudio
import time
import threading
import audioop
import argparse
import sys
sys.path.insert(0,'..')
import codec2
        

# GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='FreeDATA TEST')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--delay', dest="DELAY_BETWEEN_BURSTS", default=0, type=int)
parser.add_argument('--audiooutput', dest="AUDIO_OUTPUT", default=0, type=int) 

args = parser.parse_args()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS/1000
AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT


# AUDIO PARAMETERS
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
AUDIO_SAMPLE_RATE_TX = 48000



if AUDIO_OUTPUT_DEVICE != 0: 
    # pyaudio init
    p = pyaudio.PyAudio()
    stream_tx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_TX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER, #n_nom_modem_samples
                            output=True,
                            output_device_index=AUDIO_OUTPUT_DEVICE,  
                            )      

modes = [14,10,12]
for m in modes:

    
    freedv = cast(codec2.api.freedv_open(m), c_void_p)        
            
    n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
    mod_out = create_string_buffer(2*n_tx_modem_samples)
                        
    n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(freedv)
    mod_out_preamble = create_string_buffer(2*n_tx_preamble_modem_samples)

    n_tx_postamble_modem_samples = codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
    mod_out_postamble = create_string_buffer(2*n_tx_postamble_modem_samples)
        
    bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
    payload_per_frame = bytes_per_frame - 2

                                    
    # data binary string
    data_out = b'HELLO WORLD!'
        
    buffer = bytearray(payload_per_frame)
    # set buffersize to length of data which will be send
    buffer[:len(data_out)] = data_out

    crc = ctypes.c_ushort(codec2.api.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
    # convert crc to 2 byte hex string
    crc = crc.value.to_bytes(2, byteorder='big')
    buffer += crc        # append crc16 to buffer
    data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
               
    for i in range(1,N_BURSTS+1):

        # write preamble to txbuffer
        codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        txbuffer = bytes(mod_out_preamble)

        # create modulaton for N = FRAMESPERBURST and append it to txbuffer
        for n in range(1,N_FRAMES_PER_BURST+1):

            data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
            codec2.api.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and save it into mod_out pointer 

            txbuffer += bytes(mod_out)
            
        # append postamble to txbuffer          
        codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
        txbuffer += bytes(mod_out_postamble)

        # append a delay between bursts as audio silence
        samples_delay = int(MODEM_SAMPLE_RATE*DELAY_BETWEEN_BURSTS)
        mod_out_silence = create_string_buffer(samples_delay)    
        txbuffer += bytes(mod_out_silence)
        

        # check if we want to use an audio device or stdout
        if AUDIO_OUTPUT_DEVICE != 0: 
                
            # sample rate conversion from 8000Hz to 48000Hz
            audio = audioop.ratecv(txbuffer,2,1,MODEM_SAMPLE_RATE, AUDIO_SAMPLE_RATE_TX, None)                                           
            stream_tx.write(audio[0])

        else:
            
            # this test needs a lot of time, so we are having a look at times...
            starttime = time.time()            
 
            # print data to terminal for piping the output to other programs
            sys.stdout.buffer.write(txbuffer)    
            sys.stdout.flush()

            # and at least print the needed time to see which time we needed
            timeneeded = time.time()-starttime
            print(f"time: {timeneeded} buffer: {len(txbuffer)}", file=sys.stderr)  
       
            
# and at last check if we had an openend pyaudio instance and close it
if AUDIO_OUTPUT_DEVICE != 0: 
    stream_tx.close()
    p.terminate()
    

