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

# crc algorithm for unique audio device names
crc_algorithm = crcengine.new("crc16-ccitt-false")  # load crc16 library


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
    #sd._terminate()
    #sd._initialize()

    # log.debug("[AUD] get_audio_devices")
    with multiprocessing.Manager() as manager:
        proxy_input_devices = manager.list()
        proxy_output_devices = manager.list()
        # print(multiprocessing.get_start_method())
        proc = multiprocessing.Process(
            target=fetch_audio_devices, args=(proxy_input_devices, proxy_output_devices)
        )
        proc.start()
        proc.join()

        # additional logging for audio devices
        # log.debug("[AUD] get_audio_devices: input_devices:", list=f"{proxy_input_devices}")
        # log.debug("[AUD] get_audio_devices: output_devices:", list=f"{proxy_output_devices}")
        return list(proxy_input_devices), list(proxy_output_devices)


def device_crc(device) -> str:
    crc_hwid = crc_algorithm(bytes(f"{device}", encoding="utf-8"))
    crc_hwid = crc_hwid.to_bytes(2, byteorder="big")
    crc_hwid = crc_hwid.hex()
    return crc_hwid

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
            # Ignore some Flex Radio devices to make device selection simpler
            if name.startswith("DAX RESERVED") or name.startswith("DAX IQ"):
                continue

            max_output_channels = device["max_output_channels"]
            max_input_channels = device["max_input_channels"]

        except KeyError:
            continue
        except Exception as err:
            print(err)
            max_input_channels = 0
            max_output_channels = 0

        if max_input_channels > 0:
            hostapi_name = sd.query_hostapis(device['hostapi'])['name']

            new_input_device = {"id": device_crc(device), 
                                "name": device['name'], 
                                "api": hostapi_name,
                                "native_index":index}
            # check if device not in device list
            if new_input_device not in input_devices:
                input_devices.append(new_input_device)

        if max_output_channels > 0:
            hostapi_name = sd.query_hostapis(device['hostapi'])['name']
            new_output_device = {"id": device_crc(device), 
                                 "name": device['name'], 
                                 "api": hostapi_name,
                                 "native_index":index}
            # check if device not in device list
            if new_output_device not in output_devices:
                output_devices.append(new_output_device)


# FreeData uses the crc as id inside the configuration
# SD lib uses a numerical id which is essentially an 
# index of the device within the list
# returns (id, name)
def get_device_index_from_crc(crc, isInput: bool):
    try:
        in_devices = []
        out_devices = []

        fetch_audio_devices(in_devices, out_devices)

        if isInput:
            detected_devices = in_devices
        else:
            detected_devices = out_devices

        for i, dev in enumerate(detected_devices):
            if dev['id'] == crc:
                return (dev['native_index'], dev['name'])

    except Exception as e:
        log.warning(f"Audio device {crc} not detected ", devices=detected_devices, isInput=isInput)
        return [None, None]

def test_audio_devices(input_id: str, output_id: str) -> list:
    test_result = [False, False]
    try:
        result = get_device_index_from_crc(input_id, True)
        if result is None:
            # in_dev_index, in_dev_name = None, None
            raise ValueError(f"[Audio-Test] Invalid input device index {output_id}.")
        else:
            in_dev_index, in_dev_name = result
            sd.check_input_settings(
                device=in_dev_index,
                channels=1,
                dtype="int16",
                samplerate=48000,
            )
            test_result[0] = True
    except (sd.PortAudioError, ValueError) as e:
        log.warning(f"[Audio-Test] Input device error ({input_id}):", e=e)
        test_result[0] = False
    try:
        result = get_device_index_from_crc(output_id, False)
        if result is None:
            # out_dev_index, out_dev_name = None, None
            raise ValueError(f"[Audio-Test] Invalid output device index {output_id}.")
        else:
            out_dev_index, out_dev_name = result
            sd.check_output_settings(
                device=out_dev_index,
                channels=1,
                dtype="int16",
                samplerate=48000,
            )
            test_result[1] = True


    except (sd.PortAudioError, ValueError) as e:
        log.warning(f"[Audio-Test] Output device error ({output_id}):", e=e)
        test_result[1] = False

    sd._terminate()
    sd._initialize()
    return test_result
