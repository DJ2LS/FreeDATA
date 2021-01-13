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
import funcy
import static


AUDIO_BUFFER_SIZE = 4096
DECODE_BUFFER_SIZE = 64000

def listen():
    print("LISTEN")
    
    p = pyaudio.PyAudio()
    stream_rx = p.open(format=pyaudio.paInt16, 
                            channels=static.AUDIO_CHANNELS,
                            rate=static.AUDIO_SAMPLE_RATE,
                            frames_per_buffer=AUDIO_BUFFER_SIZE,
                            input=True,
                            input_device_index=static.AUDIO_INPUT_DEVICE,
                            ) 

    while True:
        time.sleep(0.01)

        data = stream_rx.read(AUDIO_BUFFER_SIZE,  exception_on_overflow = False)
        audio = audioop.ratecv(data,2,1,static.AUDIO_SAMPLE_RATE, static.MODEM_SAMPLE_RATE, None) 
               
        #static.AUDIO_BUFFER += audio[0]
        static.AUDIO_BUFFER += audio[0].strip(b'\x00')      
              
        #static.AUDIO_BUFFER = io.BytesIO(data.strip(b'\x00'))
        #static.AUDIO_BUFFER = io.BytesIO(audio[0].strip(b'\x00'))

 
def receive(mode):    


        libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
        c_lib = ctypes.CDLL(libname)
       
        c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte) 
        freedv = c_lib.freedv_open(mode)

        n_max_modem_samples = c_lib.freedv_get_n_max_modem_samples(freedv)
        bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)    

        bytes_out = (ctypes.c_ubyte * bytes_per_frame)
        bytes_out = bytes_out()
           
        while 1:     
            time.sleep(0.01)

                
            #if len(data) >= nin:
            #    
            print("SYNC STATUS MODE: " + str(mode) + " --- " + str(c_lib.freedv_get_rx_status()))
            #    #print(data)           
            #    print("DATA LENGTH: " + str(len(data)))
            #    print("NIN: " + str(nin))
            

            #data = static.AUDIO_BUFFER.read(BUFFER_SIZE)
            data = bytes(static.AUDIO_BUFFER)
            i = 0
            ######while i <= DECODE_BUFFER_SIZE:
            while i <= len(static.AUDIO_BUFFER):
                nin = c_lib.freedv_nin(freedv)*2
                nin = int(nin*(static.AUDIO_SAMPLE_RATE/static.MODEM_SAMPLE_RATE))
                
                data2 = data[i:((nin)+i)]
                #if len(data2) >= nin:   
                    #print("SYNC STATUS MODE: " + str(mode) + " ---> " + str(c_lib.freedv_get_rx_status()))

            #-------------------------------------------------------------------------------
                c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data2]
                nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data2)
                if nbytes == bytes_per_frame:
                    c_lib.freedv_set_sync(freedv, 0)
                    static.AUDIO_BUFFER = bytearray()
                    print("MODE: " + str(mode) + " BYTES: " + str(nbytes) + " - " + str(bytes(bytes_out)))
                    
                i = (nin) + i
            #static.AUDIO_BUFFER.seek(0)    
                
            
            
            
            
            
#-------------------------------------------------------------------------------             
FREEDV_AUDIO_THREAD = threading.Thread(target=listen, name="AUDIO LISTENER")
FREEDV_AUDIO_THREAD.start() 
                
FREEDV_DATAC3_THREAD = threading.Thread(target=receive, args=[12], name="DATAC3 Decoder")
FREEDV_DATAC3_THREAD.start()

FREEDV_700D_THREAD = threading.Thread(target=receive, args=[7], name="700D Decoder")
FREEDV_700D_THREAD.start()  
