"""
Gather information about audio devices.
"""
import multiprocessing
import sounddevice as sd
import structlog
import numpy as np
import queue
import helpers
import time

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
        proc.join(3)

        # additional logging for audio devices
        # log.debug("[AUD] get_audio_devices: input_devices:", list=f"{proxy_input_devices}")
        # log.debug("[AUD] get_audio_devices: output_devices:", list=f"{proxy_output_devices}")
        return list(proxy_input_devices), list(proxy_output_devices)


def device_crc(device) -> str:
    """Generates a CRC16 checksum for an audio device.

    This function creates a unique identifier for an audio device based on its
    name and host API. It uses a CRC16 checksum to generate a hexadecimal
    representation of the combined device name and host API.

    Args:
        device (dict): A dictionary containing the device 'name' and 'hostapi'.

    Returns:
        str: The hexadecimal representation of the CRC16 checksum.
    """
    crc_hwid = helpers.get_crc_16(bytes(f"{device['name']}.{device['hostapi']}", encoding="utf-8"))
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

    return input_devices, output_devices


def get_device_index_from_crc(crc, isInput: bool):
    """Retrieves the native device index and name from the provided CRC.

    This function searches for an audio device with the given CRC and returns
    its native index and name. It handles both input and output devices based
    on the isInput flag.

    Args:
        crc (str): The CRC of the audio device.
        isInput (bool): True if searching for an input device, False for an output device.

    Returns:
        tuple: A tuple containing the native device index and name, or (None, None) if not found.
    """
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
    """Tests the specified input and output audio devices.

    This function checks the validity and settings of the given input and
    output audio devices. It uses the device CRC to identify the devices
    and attempts to check their settings using sounddevice.

    Args:
        input_id (str): The CRC of the input audio device.
        output_id (str): The CRC of the output audio device.

    Returns:
        list: A list of booleans indicating the test results for input and output devices, respectively.
    """
    test_result = [False, False]
    try:
        result = get_device_index_from_crc(input_id, True)
        if result is None:
            # in_dev_index, in_dev_name = None, None
            raise ValueError(f"[Audio-Test] Invalid input device index {input_id}.")
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

def set_audio_volume(datalist: np.ndarray, dB: float) -> np.ndarray:
    """
    Scale values for the provided audio samples by dB.

    :param datalist: Audio samples to scale
    :type datalist: np.ndarray
    :param dB: Decibels to scale samples, constrained to the range [-50, 50]
    :type dB: float
    :return: Scaled audio samples
    :rtype: np.ndarray
    """
    try:
        dB = float(dB)
    except ValueError as e:
        print(f"[MDM] Changing audio volume failed with error: {e}")
        dB = 0.0  # 0 dB means no change

    # Clip dB value to the range [-50, 50]
    dB = np.clip(dB, -30, 20)

    # Ensure datalist is an np.ndarray
    if not isinstance(datalist, np.ndarray):
        print("[MDM] Invalid data type for datalist. Expected np.ndarray.")
        return datalist

    # Convert dB to linear scale
    scale_factor = 10 ** (dB / 20)

    # Scale samples
    scaled_data = datalist * scale_factor

    # Clip values to int16 range and convert data type
    return np.clip(scaled_data, -32768, 32767).astype(np.int16)


def normalize_audio(datalist: np.ndarray) -> np.ndarray:
    """
    Normalize the audio samples so the loudest value reaches 95% of the maximum possible value for np.int16
    :param datalist: Audio samples to normalize
    :type datalist: np.ndarray
    :return: Normalized audio samples, clipped to the range of int16
    :rtype: np.ndarray
    """
    if not isinstance(datalist, np.ndarray):
        #print("[MDM] Invalid datalist type. Expected np.ndarray.")
        return datalist

    # Ensure datalist is not empty
    if datalist.size == 0:
        #print("[MDM] Datalist is empty. Returning unmodified.")
        return datalist

    # Find the maximum absolute value in the data
    max_value = np.max(np.abs(datalist))

    # If max_value is 0, return the datalist (avoid division by zero)
    if max_value == 0:
        #print("[MDM] Max value is zero. Cannot normalize. Returning unmodified.")
        return datalist

    # Define the target max value as 95% of the maximum for np.int16
    target_max_value = int(32767 * 0.95)

    # Compute the normalization factor
    normalization_factor = target_max_value / max_value

    # Normalize the audio data
    normalized_data = datalist * normalization_factor

    # Clip to the int16 range and cast
    normalized_data = np.clip(normalized_data, -32768, 32767).astype(np.int16)

    # Debug information: normalization factor, loudest value before, and after normalization
    loudest_before = max_value
    loudest_after = np.max(np.abs(normalized_data))
    # print(f"[AUDIO] Normalization factor: {normalization_factor:.6f}, Loudest before: {loudest_before}, Loudest after: {loudest_after}")

    return normalized_data


# Global variables to manage channel status
CHANNEL_BUSY_DELAY = 0  # Counter for channel busy delay
SLOT_DELAY = [0] * 5  # Counters for delays in each slot

# Constants for delay logic
DELAY_INCREMENT = 2  # Amount to increase delay
MAX_DELAY = 200  # Maximum allowable delay

# Predefined frequency ranges (slots) for FFT analysis
# These ranges are based on an FFT length of 800 samples
SLOT_RANGES = [
    (0, 65),  # Slot 1: Frequency range from 0 to 65
    (65, 120),  # Slot 2: Frequency range from 65 to 120
    (120, 176),  # Slot 3: Frequency range from 120 to 176
    (176, 231),  # Slot 4: Frequency range from 176 to 231
    (231, 315)  # Slot 5: Frequency range from 231 to 315
]

# Initialize a queue to store FFT results for visualization
fft_queue = queue.Queue()

# Variable to track the time of the last RMS calculation
last_rms_time = 0

def prepare_data_for_fft(data, target_length_samples=800):
    """
    Prepare the input data for FFT by ensuring it meets the required length.

    Parameters:
    - data: numpy.ndarray of type np.int16, representing the audio data.
    - target_length_samples: int, the desired length of the data in samples.

    Returns:
    - numpy.ndarray of type np.int16 with a length of target_length_samples.
    """
    # Check if the input data type is np.int16
    if data.dtype != np.int16:
        raise ValueError("Audio data must be of type np.int16")

    # If data is shorter than the target length, pad with zeros
    if len(data) < target_length_samples:
        return np.pad(data, (0, target_length_samples - len(data)), 'constant', constant_values=(0,))
    else:
        # If data is longer or equal to the target length, truncate it
        return data[:target_length_samples]

def calculate_rms_dbfs(data):
    """
    Calculate the Root Mean Square (RMS) value of the audio data and
    convert it to dBFS (decibels relative to full scale).

    Parameters:
    - data: numpy.ndarray of type np.int16, representing the audio data.

    Returns:
    - float: RMS value in dBFS. Returns -100 if the RMS value is 0.
    """
    # Compute the RMS value using int32 to prevent overflow
    rms = np.sqrt(np.mean(np.square(data, dtype=np.int32), dtype=np.float64))
    # Convert the RMS value to dBFS
    return 20 * np.log10(rms / 32768) if rms > 0 else -100


def calculate_fft(data, fft_queue, states) -> None:
    """Calculates the FFT of audio data and updates channel busy status.

    This function performs FFT on the provided audio data, identifies
    significant frequency components, and updates the channel busy status
    based on activity within predefined frequency slots. It also calculates
    and updates the RMS level of the audio data.

    Args:
        data (np.ndarray): The audio data as a NumPy array.
        fft_queue (queue.Queue): A queue to store FFT results for visualization.
        states (StateManager): The state manager object to update channel busy status.
    """
    global CHANNEL_BUSY_DELAY, last_rms_time

    try:
        # Prepare the data for FFT processing by ensuring it meets the target length
        data = prepare_data_for_fft(data)

        # Compute the real FFT of the audio data
        fftarray = np.fft.rfft(data)

        # Calculate the amplitude spectrum in decibels (dB)
        dfft = 10.0 * np.log10(np.abs(fftarray) + 1e-12)  # Adding a small constant to avoid log(0)

        # Compute the average amplitude of the spectrum
        avg_amplitude = np.mean(dfft)

        # Set the threshold for significant frequency components; adjust the offset as needed
        threshold = avg_amplitude + 13

        # Identify frequency components that exceed the threshold
        significant_frequencies = dfft > threshold

        # Check if the system is neither transmitting nor receiving
        not_transmitting = not states.isTransmitting()
        not_receiving = not states.is_receiving_codec2_signal()

        if not_transmitting:
            # Highlight significant frequencies in the dfft array
            dfft[significant_frequencies] = 100

            # Get the current time
            current_time = time.time()

            # Update the RMS value every second
            if current_time - last_rms_time >= 1.0:
                # Calculate the RMS value in dBFS
                audio_dbfs = calculate_rms_dbfs(data)

                # Update the state with the new RMS value
                states.set("audio_dbfs", audio_dbfs)

                # Update the last RMS calculation time
                last_rms_time = current_time

        # Convert the dfft array to integers for further processing
        dfft = dfft.astype(int)

        # Convert the dfft array to a list for queue insertion
        dfftlist = dfft.tolist()

        # Initialize the slot busy status list
        slotbusy = [False] * len(SLOT_RANGES)

        # Flag to determine if additional delay should be added
        addDelay = False

        # Iterate over each slot range to detect activity
        for slot, (range_start, range_end) in enumerate(SLOT_RANGES):
            # Check if any frequency in the slot exceeds the threshold
            if np.any(significant_frequencies[range_start:range_end]) and not_transmitting and not_receiving:
                # Mark that additional delay should be added
                addDelay = True

                # Set the current slot as busy
                slotbusy[slot] = True

                # Increment the slot delay, ensuring it does not exceed the maximum
                SLOT_DELAY[slot] = min(SLOT_DELAY[slot] + DELAY_INCREMENT, MAX_DELAY)
            else:
                # Decrement the slot delay, ensuring it does not go below zero
                SLOT_DELAY[slot] = max(SLOT_DELAY[slot] - 1, 0)

                # Set the slot busy status based on the current delay
                slotbusy[slot] = SLOT_DELAY[slot] > 0

        # Update the state with the current slot busy statuses
        states.set_channel_slot_busy(slotbusy)

        if addDelay:
            # Set the channel busy condition due to traffic
            states.set_channel_busy_condition_traffic(True)

            # Increment the channel busy delay, ensuring it does not exceed the maximum
            CHANNEL_BUSY_DELAY = min(CHANNEL_BUSY_DELAY + DELAY_INCREMENT, MAX_DELAY)
        else:
            # Decrement the channel busy delay, ensuring it does not go below zero
            CHANNEL_BUSY_DELAY = max(CHANNEL_BUSY_DELAY - 1, 0)

            # If the channel busy delay has reset, clear the busy condition
            if CHANNEL_BUSY_DELAY == 0:
                states.set_channel_busy_condition_traffic(False)

        # Clear any existing items in the FFT queue
        while not fft_queue.empty():
            fft_queue.get()

        # Add the processed dfft list to the FFT queue, limited to the first 315 elements
        fft_queue.put(dfftlist[:315])

    except Exception as err:
        # Log any exceptions that occur during the FFT calculation
        print(f"[MDM] calculate_fft: Exception: {err}")


def terminate():
    """Terminates the audio instance.

    This function terminates the sounddevice instance if it's initialized,
    releasing audio resources and preventing potential issues during shutdown.
    """
    log.warning("[SHUTDOWN] terminating audio instance...")
    if sd._initialized:
        sd._terminate()
