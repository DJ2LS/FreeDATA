 #!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ctypes
from ctypes import *
import pathlib
import pyaudio
import time
import threading
import audioop
import io



AUDIO_OUTPUT_DEVICE = 2
AUDIO_SAMPLE_RATE_TX = 44100

# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = 8000

mode = 12
data_out = b'HELLO WORLD!'
        #-------------------------------------------- LOAD FREEDV
             
libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
c_lib = ctypes.CDLL(libname)

        #--------------------------------------------CREATE PYAUDIO  INSTANCE
        
p = pyaudio.PyAudio()
        
        #--------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE
        
AUDIO_SAMPLE_RATE_TX = int(p.get_device_info_by_index(AUDIO_OUTPUT_DEVICE)['defaultSampleRate'])
        
        #--------------------------------------------OPEN AUDIO CHANNEL TX

stream_tx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_TX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER, #n_nom_modem_samples
                            output=True,
                            output_device_index=AUDIO_OUTPUT_DEVICE,  
                            )  
             


c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
freedv = c_lib.freedv_open(mode)
bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
payload_per_frame = bytes_per_frame -2
n_nom_modem_samples = c_lib.freedv_get_n_nom_modem_samples(freedv)
n_tx_modem_samples = c_lib.freedv_get_n_tx_modem_samples(freedv) #get n_tx_modem_samples which defines the size of the modulation object # --> *2

          
mod_out = ctypes.c_short * n_tx_modem_samples
mod_out = mod_out()

data_list = [data_out[i:i+payload_per_frame] for i in range(0, len(data_out), payload_per_frame)] # split incomming bytes to size of 30bytes, create a list and loop through it  
data_list_length = len(data_list)
for i in range(data_list_length): # LOOP THROUGH DATA LIST
            
            if mode < 10: # don't generate CRC16 for modes 0 - 9
                
                buffer = bytearray(bytes_per_frame) # use this if no CRC16 checksum is required
                buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send
                              
            if mode >= 10: #generate CRC16 for modes 10-12..
                
                buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
                buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send

                crc = ctypes.c_ushort(c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
                buffer += crc        # append crc16 to buffer    
                
            data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
            
            c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer     
            #print(bytes(mod_out).strip(b'\x00'))
            
            modulation = bytes(mod_out)
            if mode == 7:
                mod_with_preamble = modulation[:len(modulation)] + modulation # double transmission in one audio burst

            if mode == 12:
                mod_with_preamble = modulation[:0] + modulation # no preamble


            audio = audioop.ratecv(mod_with_preamble,2,1,MODEM_SAMPLE_RATE, AUDIO_SAMPLE_RATE_TX, None)                                           
            stream_tx.write(audio[0]) 


stream_tx.close()
p.terminate()
