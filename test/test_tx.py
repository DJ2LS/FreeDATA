#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ctypes
from ctypes import *
import pathlib
import pyaudio
import time
import argparse
import sys
sys.path.insert(0,'..')
from tnc import codec2
import numpy as np

# GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=1, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=1, type=int)
parser.add_argument('--delay', dest="DELAY_BETWEEN_BURSTS", default=500, type=int,
                    help="delay between bursts in ms")
parser.add_argument('--mode', dest="FREEDV_MODE", type=str, choices=['datac0', 'datac1', 'datac3'])
parser.add_argument('--audiodev', dest="AUDIO_OUTPUT_DEVICE", default=-1, type=int,
                    help="audio output device number to use, use -2 to automatically select a loopback device") 
parser.add_argument('--list', dest="LIST", action="store_true", help="list audio devices by number and exit")  
parser.add_argument('--testframes', dest="TESTFRAMES", action="store_true", default=False, help="list audio devices by number and exit")  


args = parser.parse_args()

if args.LIST:
    p = pyaudio.PyAudio()
    for dev in range(0,p.get_device_count()):
        print("audiodev: ", dev, p.get_device_info_by_index(dev)["name"])
    quit()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS/1000
AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT_DEVICE

MODE = codec2.FREEDV_MODE[args.FREEDV_MODE].value

# AUDIO PARAMETERS
AUDIO_FRAMES_PER_BUFFER = 2400
MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
AUDIO_SAMPLE_RATE_TX = 48000
assert (AUDIO_SAMPLE_RATE_TX % MODEM_SAMPLE_RATE) == 0

# check if we want to use an audio device then do an pyaudio init
if AUDIO_OUTPUT_DEVICE != -1: 
    p = pyaudio.PyAudio()
    # auto search for loopback devices
    if AUDIO_OUTPUT_DEVICE == -2:
        loopback_list = []
        for dev in range(0,p.get_device_count()):
            if 'Loopback: PCM' in p.get_device_info_by_index(dev)["name"]:
                loopback_list.append(dev)
        if len(loopback_list) >= 2:
            AUDIO_OUTPUT_DEVICE = loopback_list[1] #0  = RX   1 = TX
            print(f"loopback_list tx: {loopback_list}", file=sys.stderr)
        else:
            quit()        
    print(f"AUDIO OUTPUT DEVICE: {AUDIO_OUTPUT_DEVICE} DEVICE: {p.get_device_info_by_index(AUDIO_OUTPUT_DEVICE)['name']} \
            AUDIO SAMPLE RATE: {AUDIO_SAMPLE_RATE_TX}", file=sys.stderr)

    # pyaudio init
    stream_tx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_TX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER, #n_nom_modem_samples
                            output=True,
                            output_device_index=AUDIO_OUTPUT_DEVICE
                            )      
                                
                                
resampler = codec2.resampler()

# data binary string
if args.TESTFRAMES:
    data_out = bytearray(14)
    data_out[:1]   = bytes([255])
    data_out[1:2]  = bytes([1])
    data_out[2:]  = b'HELLO WORLD'
    
else:
    data_out = b'HELLO WORLD!'


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
        
        print(f"TX BURST: {i}/{N_BURSTS} FRAME: {n}/{N_FRAMES_PER_BURST}", file=sys.stderr)
    
    # append postamble to txbuffer          
    codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
    txbuffer += bytes(mod_out_postamble)

    # append a delay between bursts as audio silence
    samples_delay = int(MODEM_SAMPLE_RATE*DELAY_BETWEEN_BURSTS)
    mod_out_silence = create_string_buffer(samples_delay*2)
    txbuffer += bytes(mod_out_silence)
    #print(f"samples_delay: {samples_delay} DELAY_BETWEEN_BURSTS: {DELAY_BETWEEN_BURSTS}", file=sys.stderr)

    # resample up to 48k (resampler works on np.int16)
    x = np.frombuffer(txbuffer, dtype=np.int16)
    txbuffer_48k = resampler.resample8_to_48(x)
    
    # check if we want to use an audio device or stdout
    if AUDIO_OUTPUT_DEVICE != -1:
        # Gotcha: we have to convert from np.int16 to Python "bytes"
        stream_tx.write(txbuffer_48k.tobytes())
    else:
        # print data to terminal for piping the output to other programs
        sys.stdout.buffer.write(txbuffer_48k)    
        sys.stdout.flush()


# and at last check if we had an opened pyaudio instance and close it
if AUDIO_OUTPUT_DEVICE != -1:
    time.sleep(stream_tx.get_output_latency())
    stream_tx.stop_stream()
    stream_tx.close()
    p.terminate()

