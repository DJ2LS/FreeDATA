#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import numpy as np
import audioop
import miniaudio


p = pyaudio.PyAudio()

volume = 0.5
fshigh = 48000
fslow = 8000
duration = 50.0
f = 440.0


samples_48000 = (np.sin(2*np.pi*np.arange(fshigh*duration)*f/fshigh)).astype(np.float32)
samples_8000 = (np.sin(2*np.pi*np.arange(fslow*duration)*f/fslow)).astype(np.float32)
samples_converted = audioop.ratecv(samples_48000,2,1,fshigh, fslow , None)       
samples_converted = bytes(samples_converted[0])

converted_frames = miniaudio.convert_frames(miniaudio.SampleFormat.FLOAT32, 1, 48000, bytes(samples_48000), miniaudio.SampleFormat.FLOAT32, 1, 8000)

converted_frames = bytes(converted_frames)


print(type(samples_8000))
print(type(samples_converted))
print(type(converted_frames))
stream = p.open(format=pyaudio.paFloat32,
                            channels=2,
                            rate=fshigh,
                            output=True,
                            output_device_index=0  #static.AUDIO_OUTPUT_DEVICE
                            ) 
print("original 48000Hz sample")                            
stream.write(samples_48000)
print("original 8000Hz sample")   
stream.write(samples_8000)
print("48000Hz to 8000Hz with audioop")   
stream.write(samples_converted)
print("48000Hz to 8000Hz with miniaudio") 
stream.write(converted_frames)


stream.stop_stream()
stream.close()
p.terminate()                            
