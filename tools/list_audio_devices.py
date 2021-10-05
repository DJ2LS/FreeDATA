#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pyaudio


def list_audio_devices():
    p = pyaudio.PyAudio()
    devices = []
    print("--------------------------------------------------------------------")
    for x in range(0, p.get_device_count()):
        devices.append(f"{x} - {p.get_device_info_by_index(x)['name']}")
        
    for line in devices:
        print(line) 
        

        
        
        
        
        
        
list_audio_devices()
