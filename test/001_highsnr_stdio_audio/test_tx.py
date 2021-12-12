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

# GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--delay', dest="DELAY_BETWEEN_BURSTS", default=0, type=int)
parser.add_argument('--mode', dest="FREEDV_MODE", default=14, type=int)
parser.add_argument('--audiooutput', dest="AUDIO_OUTPUT", default=0, type=int) 

args = parser.parse_args()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS/1000
AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT
MODE = args.FREEDV_MODE


# AUDIO PARAMETERS
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = 8000
AUDIO_SAMPLE_RATE_TX = 48000

# check if we want to use an audio device then do an pyaudio init
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
                                
                                
# data binary string
data_out = b'HELLO WORLD!'


sys.path.insert(0,'..')
import codec2
        
# ----------------------------------------------------------------



# open codec2 instance        
freedv = cast(codec2.api.freedv_open(MODE), c_void_p)

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


# create buffer for data
buffer = bytearray(payload_bytes_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
buffer[:len(data_out)] = data_out # set buffersize to length of data which will be send

# create crc for data frame - we are using the crc function shipped with codec2 to avoid 
# crc algorithm incompatibilities
crc = ctypes.c_ushort(codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame))     # generate CRC16
crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
buffer += crc        # append crc16 to buffer    


print(f"TOTAL BURSTS: {N_BURSTS} TOTAL FRAMES_PER_BURST: {N_FRAMES_PER_BURST}", file=sys.stderr)

for i in range(1,N_BURSTS+1):

    # write preamble to txbuffer
    codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
    txbuffer = bytes(mod_out_preamble)

    # create modulaton for N = FRAMESPERBURST and append it to txbuffer
    for n in range(1,N_FRAMES_PER_BURST+1):

        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
        codec2.api.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and save it into mod_out pointer 

        txbuffer += bytes(mod_out)
        
        print(f"BURST: {i}/{N_BURSTS} FRAME: {n}/{N_FRAMES_PER_BURST}", file=sys.stderr)
    
    # append postamble to txbuffer          
    codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
    txbuffer += bytes(mod_out_postamble)

    # append a delay between bursts as audio silence
    samples_delay = int(MODEM_SAMPLE_RATE*DELAY_BETWEEN_BURSTS)
    mod_out_silence = create_string_buffer(samples_delay)    
    txbuffer += bytes(mod_out_silence)
    print(f"samples_delay: {samples_delay} DELAY_BETWEEN_BURSTS: {DELAY_BETWEEN_BURSTS}", file=sys.stderr)
    
    # check if we want to use an audio device or stdout
    if AUDIO_OUTPUT_DEVICE != 0: 
        
        # sample rate conversion from 8000Hz to 48000Hz
        audio = audioop.ratecv(txbuffer,2,1,MODEM_SAMPLE_RATE, AUDIO_SAMPLE_RATE_TX, None)                                           
        stream_tx.write(audio[0])

    else:
        # print data to terminal for piping the output to other programs
        sys.stdout.buffer.write(txbuffer)    
        sys.stdout.flush()


# and at last check if we had an openend pyaudio instance and close it
if AUDIO_OUTPUT_DEVICE != 0: 
    stream_tx.close()
    p.terminate()
