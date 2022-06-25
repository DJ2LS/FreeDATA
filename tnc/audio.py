"""
Gather information about audio devices.
"""
import atexit
import multiprocessing

import sounddevice as sd

atexit.register(sd._terminate)


def get_audio_devices():
    """
    return list of input and output audio devices in own process to avoid crashes of portaudio on raspberry pi

    also uses a process data manager
    """
    # we need to run this on Windows for multiprocessing support
    # multiprocessing.freeze_support()
    # multiprocessing.get_context("spawn")

    # we need to reset and initialize sounddevice before running the multiprocessing part.
    # If we are not doing this at this early point, not all devices will be displayed
    sd._terminate()
    sd._initialize()

    with multiprocessing.Manager() as manager:
        proxy_input_devices = manager.list()
        proxy_output_devices = manager.list()
        # print(multiprocessing.get_start_method())
        proc = multiprocessing.Process(
            target=fetch_audio_devices, args=(proxy_input_devices, proxy_output_devices)
        )
        proc.start()
        proc.join()

        # The use of set forces the list to contain only unique entries.
        return list(set(proxy_input_devices)), list(set(proxy_output_devices))


def fetch_audio_devices(input_devices, output_devices):
    """
    get audio devices from portaudio

    Args:
      input_devices: proxy variable for input devices
      output_devices: proxy variable for output devices

    Returns:

    """
    devices = sd.query_devices(device=None, kind=None)
    for index, device in enumerate(devices):
        # Use a try/except block because Windows doesn't have an audio device range
        try:
            name = device["name"]

            max_output_channels = device["max_output_channels"]
            max_input_channels = device["max_input_channels"]

        except Exception as err:
            print(err)
            max_input_channels = 0
            max_output_channels = 0
            name = ""

        if max_input_channels > 0:
            input_devices.append({"id": index, "name": name})
        if max_output_channels > 0:
            output_devices.append({"id": index, "name": name})
