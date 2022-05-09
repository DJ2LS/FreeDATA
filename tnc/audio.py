
import json
import sys
import multiprocessing
import sounddevice as sd
import atexit

atexit.register(sd._terminate)

def get_audio_devices():



    """
    return list of input and output audio devices in own process to avoid crashes of portaudio on raspberry pi

    also uses a process data manager
    """
    # we need to run this on windows for multiprocessing support
    # multiprocessing.freeze_support()
    #multiprocessing.get_context('spawn')

    # we need to reset and initialize sounddevice before running the multiprocessing part.
    # If we are not doing this at this early point, not all devices will be displayed
    sd._terminate()
    sd._initialize()

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

    devices = sd.query_devices(device=None, kind=None)
    index = 0
    for device in devices:
    #for i in range(0, p.get_device_count()):
        # we need to do a try exception, beacuse for windows theres no audio device range
        try:
            name = device["name"]

            maxOutputChannels = device["max_output_channels"]
            maxInputChannels = device["max_input_channels"]

        except Exception as e:
            print(e)
            maxInputChannels = 0
            maxOutputChannels = 0
            name = ''

        if maxInputChannels > 0:
            input_devices.append({"id": index, "name": str(name)})
        if maxOutputChannels > 0:
            output_devices.append({"id": index, "name": str(name)})
        index += 1

