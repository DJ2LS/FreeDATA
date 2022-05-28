#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pyaudio


def list_audio_devices():
    p = pyaudio.PyAudio()
    print("--------------------------------------------------------------------")
    devices = [
        f"{x} - {p.get_device_info_by_index(x)['name']}"
        for x in range(p.get_device_count())
    ]

    for line in devices:
        print(line)


list_audio_devices()
