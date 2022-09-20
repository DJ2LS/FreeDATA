"""
Gather information about audio devices.
"""
import atexit
import multiprocessing

import crcengine
import sounddevice as sd
import structlog

atexit.register(sd._terminate)

log = structlog.get_logger("audio")


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

    log.error("[AUD] get_audio_devices")
    with multiprocessing.Manager() as manager:
        proxy_input_devices = manager.list()
        proxy_output_devices = manager.list()
        # print(multiprocessing.get_start_method())
        proc = multiprocessing.Process(
            target=fetch_audio_devices, args=(proxy_input_devices, proxy_output_devices)
        )
        proc.start()
        proc.join()

        log.error(f"[AUD] get_audio_devices: input_devices: {proxy_input_devices}")
        log.error(f"[AUD] get_audio_devices: output_devices: {proxy_output_devices}")
        return list(proxy_input_devices), list(proxy_output_devices)


def device_crc(device) -> str:
    crc_algorithm = crcengine.new("crc16-ccitt-false")  # load crc8 library
    crc_hwid = crc_algorithm(bytes(f"{device}", encoding="utf-8"))
    crc_hwid = crc_hwid.to_bytes(2, byteorder="big")
    crc_hwid = crc_hwid.hex()
    return f"{device['name']} [{crc_hwid}]"


def fetch_audio_devices(input_devices, output_devices):
    """
    get audio devices from portaudio

    Args:
      input_devices: proxy variable for input devices
      output_devices: proxy variable for output devices

    Returns:

    """
    devices = sd.query_devices(device=None, kind=None)

    # The use of set forces the list to contain only unique entries.
    input_devs = set()
    output_devs = set()

    for device in devices:
        # Use a try/except block because Windows doesn't have an audio device range
        try:
            name = device["name"]

            max_output_channels = device["max_output_channels"]
            max_input_channels = device["max_input_channels"]

        except KeyError:
            continue
        except Exception as err:
            print(err)
            max_input_channels = 0
            max_output_channels = 0
            name = ""

        if max_input_channels > 0:
            input_devs.add(device_crc(device))
        if max_output_channels > 0:
            output_devs.add(device_crc(device))

    for index, item in enumerate(input_devs):
        input_devices.append({"id": index, "name": item})
    for index, item in enumerate(output_devs):
        output_devices.append({"id": index, "name": item})
