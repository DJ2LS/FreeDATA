
import json
import sys
import multiprocessing
####################################################
# https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time
# https://github.com/DJ2LS/FreeDATA/issues/22
# we need to have a look at this if we want to run this on Windows and MacOS !
# Currently it seems, this is a Linux-only problem

from ctypes import *
from contextlib import contextmanager
import pyaudio

AUDIO_DEVICES = multiprocessing.Queue()



ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)
    
# with noalsaerr():
#   p = pyaudio.PyAudio()
#####################################################

def get_audio_devices():

    p = multiprocessing.Process(target=update_audio_devices)
    p.start()
    p.join()
    audio_devices = AUDIO_DEVICES.get()

    return audio_devices    
    
def update_audio_devices():
    # UPDATE LIST OF AUDIO DEVICES    
    try:
    # we need to "try" this, because sometimes libasound.so isn't in the default place                   
        # try to supress error messages
        with noalsaerr(): # https://github.com/DJ2LS/FreeDATA/issues/22
            p = pyaudio.PyAudio()
    # else do it the default way
    except Exception as e:
        p = pyaudio.PyAudio()
    
    input_devices = []
    output_devices = []
    
    for i in range(0, p.get_device_count()):
        # we need to do a try exception, beacuse for windows theres now audio device range
        try:
            maxInputChannels = p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')
            maxOutputChannels = p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')
            name = p.get_device_info_by_host_api_device_index(0, i).get('name')
        except:
            maxInputChannels = 0
            maxOutputChannels = 0
            name = ''

        if maxInputChannels > 0:
            input_devices.append({"id": i, "name": str(name)})
        if maxOutputChannels > 0:
            output_devices.append({"id": i, "name": str(name)})
    
    p.terminate()

    AUDIO_DEVICES.put([input_devices, output_devices])
    return [input_devices, output_devices]

