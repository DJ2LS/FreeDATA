
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


ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    """

    Args:
      filename: 
      line: 
      function: 
      err: 
      fmt: 

    Returns:

    """
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    """ """
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)
    
# with noalsaerr():
#   p = pyaudio.PyAudio()
#####################################################

def get_audio_devices():
    """
    return list of input and output audio devices in own process to avoid crashes of portaudio on raspberry pi
    
    also uses a process data manager
    """
    # we need to run this on windows for multiprocessing support
    # multiprocessing.freeze_support()
    #multiprocessing.get_context('spawn')

    with multiprocessing.Manager() as manager:
        proxy_input_devices = manager.list()
        proxy_output_devices = manager.list()
        #print(multiprocessing.get_start_method())
        p = multiprocessing.Process(target=fetch_audio_devices, args=(proxy_input_devices, proxy_output_devices))
        p.start()
        p.join()

        return list(proxy_input_devices), list(proxy_output_devices)   

def fetch_audio_devices(input_devices, output_devices):
    """
    get audio devices from portaudio
    
    Args:
      input_devices: proxy variable for input devices
      output_devices: proxy variable for outout devices

    Returns:

    """
    # UPDATE LIST OF AUDIO DEVICES    
    try:
    # we need to "try" this, because sometimes libasound.so isn't in the default place                   
        # try to supress error messages
        with noalsaerr(): # https://github.com/DJ2LS/FreeDATA/issues/22
            p = pyaudio.PyAudio()
    # else do it the default way
    except Exception as e:
        p = pyaudio.PyAudio()
    
    #input_devices = []
    #output_devices = []
    
    for i in range(0, p.get_device_count()):
        # we need to do a try exception, beacuse for windows theres no audio device range
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
