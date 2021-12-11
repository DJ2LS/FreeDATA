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

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--frames', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--delay', dest="DELAY_BETWEEN_BURSTS", default=0, type=int)
parser.add_argument('--mode', dest="FREEDV_MODE", default=0, type=int)
parser.add_argument('--output', dest="DATA_OUTPUT", type=str)  
parser.add_argument('--audiooutput', dest="AUDIO_OUTPUT", default=0, type=int) 

args = parser.parse_args()




N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS/1000
DATA_OUTPUT = args.DATA_OUTPUT


AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT


# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = 8000

mode = args.FREEDV_MODE
data_out = b'HELLO WORLD!'



print(N_BURSTS)
print(N_FRAMES_PER_BURST)





        #-------------------------------------------- LOAD FREEDV
             
libname = "libcodec2.so"
c_lib = ctypes.CDLL(libname)

        #--------------------------------------------CREATE PYAUDIO  INSTANCE
        
        
        #--------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE
        
        
        #--------------------------------------------OPEN AUDIO CHANNEL TX

if DATA_OUTPUT == "audio":          
    p = pyaudio.PyAudio()
    stream_tx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_TX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER, #n_nom_modem_samples
                            output=True,
                            output_device_index=AUDIO_OUTPUT_DEVICE,  
                            )  
    AUDIO_SAMPLE_RATE_TX = int(p.get_device_info_by_index(AUDIO_OUTPUT_DEVICE)['defaultSampleRate'])
             


c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
freedv = c_lib.freedv_open(mode)
bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
payload_per_frame = bytes_per_frame -2
n_nom_modem_samples = c_lib.freedv_get_n_nom_modem_samples(freedv)
n_tx_modem_samples = c_lib.freedv_get_n_tx_modem_samples(freedv) #get n_tx_modem_samples which defines the size of the modulation object # --> *2
    
mod_out = ctypes.c_short * n_tx_modem_samples
mod_out = mod_out()
mod_out_preamble = ctypes.c_short * (1760*2) #1760 for mode 10,11,12 #4000 for mode 9
mod_out_preamble = mod_out_preamble()
        
buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
buffer[:len(data_out)] = data_out # set buffersize to length of data which will be send

crc = ctypes.c_ushort(c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
buffer += crc        # append crc16 to buffer    


print("BURSTS: " + str(N_BURSTS) + " FRAMES: " + str(N_FRAMES_PER_BURST) )

for i in range(0,N_BURSTS):

    c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble);

    txbuffer = bytearray()
    txbuffer += bytes(mod_out_preamble)

    for n in range(0,N_FRAMES_PER_BURST):

        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
        c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer 

        txbuffer += bytes(mod_out)
    
    if DATA_OUTPUT == "audio":          
        audio = audioop.ratecv(txbuffer,2,1,MODEM_SAMPLE_RATE, AUDIO_SAMPLE_RATE_TX, None)                                           
        stream_tx.write(audio[0])
        txbuffer = bytearray()
    else:
        sys.stdout.buffer.write(txbuffer)    # print data to terminal for piping the output to other programs
        sys.stdout.flush()
        txbuffer = bytearray()

    time.sleep(DELAY_BETWEEN_BURSTS)

if DATA_OUTPUT == "audio":          
    stream_tx.close()
    p.terminate()
