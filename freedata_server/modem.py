#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel

import queue
import time
import codec2
import numpy as np
import sounddevice as sd
import structlog
import cw
import audio
import demodulator
import modulator

TESTMODE = False

class RF:
    """Handles FreeDATA modem functionality.

    This class manages the audio interface, modulation, demodulation, and
    transmission of FreeDATA signals. It interacts with the demodulator,
    modulator, audio devices, and radio manager to handle data transmission
    and reception.
    """

    log = structlog.get_logger("RF")

    def __init__(self, config, event_manager, fft_queue, service_queue, states, radio_manager) -> None:
        """Initializes the RF modem.

        Args:
            config (dict): Configuration dictionary.
            event_manager (EventManager): Event manager instance.
            fft_queue (Queue): Queue for FFT data.
            service_queue (Queue): Queue for freedata_server service commands.
            states (StateManager): State manager instance.
            radio_manager (RadioManager): Radio manager instance.
        """
        self.config = config
        self.service_queue = service_queue
        self.states = states
        self.event_manager = event_manager
        self.radio = radio_manager
        self.sampler_avg = 0
        self.buffer_avg = 0

        # these are crc ids now
        self.audio_input_device = config['AUDIO']['input_device']
        self.audio_output_device = config['AUDIO']['output_device']



        self.radiocontrol = config['RADIO']['control']
        self.rigctld_ip = config['RIGCTLD']['ip']
        self.rigctld_port = config['RIGCTLD']['port']


        self.tx_audio_level = config['AUDIO']['tx_audio_level']
        self.rx_audio_level = config['AUDIO']['rx_audio_level']


        self.ptt_state = False
        self.enqueuing_audio = False # set to True, while we are processing audio

        self.AUDIO_SAMPLE_RATE = 48000
        self.modem_sample_rate = codec2.api.FREEDV_FS_8000

        # 8192 Let's do some tests with very small chunks for TX
        # 8 * (self.AUDIO_SAMPLE_RATE/self.modem_sample_rate) == 48
        self.AUDIO_CHANNELS = 1
        self.MODE = 0
        self.rms_counter = 0

        self.audio_out_queue = queue.Queue()

        # Make sure our resampler will work
        assert (self.AUDIO_SAMPLE_RATE / self.modem_sample_rate) == codec2.api.FDMDV_OS_48  # type: ignore

        self.audio_received_queue = queue.Queue()
        self.data_queue_received = queue.Queue()
        self.fft_queue = fft_queue

        self.demodulator = demodulator.Demodulator(self.config, 
                                            self.audio_received_queue, 
                                            self.data_queue_received,
                                            self.states,
                                            self.event_manager,
                                            self.service_queue,
                                            self.fft_queue
                                                   )

        self.modulator = modulator.Modulator(self.config)

    def start_modem(self):
        """Starts the modem.

        This method initializes the audio devices and starts the demodulator.
        In test mode, it bypasses audio initialization. It raises a
        RuntimeError if audio initialization fails.

        Returns:
            bool: True if the modem started successfully.

        Raises:
            RuntimeError: If audio device initialization fails.
        """
        if TESTMODE:
            return True
        else:
            if not self.init_audio():
                raise RuntimeError("Unable to init audio devices")
            self.demodulator.start(self.sd_input_stream)

        return True

    def stop_modem(self):
        """Stops the modem.

        This method stops the FreeDATA freedata_server service, closes audio input and
        output streams, and handles any exceptions during the process.
        """
        try:
            # let's stop the freedata_server service
            self.service_queue.put("stop")
            # simulate audio class active state for reducing cli output
            # self.stream = lambda: None
            # self.stream.active = False
            # self.stream.stop
            self.sd_input_stream.close()
            self.sd_output_stream.close()
        except Exception as e:
            self.log.error("[MDM] Error stopping freedata_server", e=e)

    def init_audio(self):
        """Initializes the audio input and output streams.

        This method retrieves the audio device indices based on their CRC
        checksums from the configuration, sets up the default audio
        parameters, initializes the Codec2 resampler, and starts the
        SoundDevice input and output streams with appropriate callbacks and
        buffer sizes. It logs information about the selected audio devices
        and handles potential exceptions during initialization.

        Returns:
            bool: True if audio initialization was successful, False otherwise.
        """
        self.log.info(f"[MDM] init: get audio devices", input_device=self.audio_input_device,
                      output_device=self.audio_output_device)
        try:
            result = audio.get_device_index_from_crc(self.audio_input_device, True)
            if result is None:
                raise ValueError("Invalid input device")
            else:
                in_dev_index, in_dev_name = result

            result = audio.get_device_index_from_crc(self.audio_output_device, False)
            if result is None:
                raise ValueError("Invalid output device")
            else:
                out_dev_index, out_dev_name = result

            self.log.info(f"[MDM] init: receiving audio from '{in_dev_name}'")
            self.log.info(f"[MDM] init: transmiting audio on '{out_dev_name}'")
            self.log.debug("[MDM] init: starting pyaudio callback and decoding threads")

            sd.default.samplerate = self.AUDIO_SAMPLE_RATE
            sd.default.device = (in_dev_index, out_dev_index)

            # init codec2 resampler
            self.resampler = codec2.resampler()

            # SoundDevice audio input stream
            self.sd_input_stream = sd.InputStream(
                channels=1,
                dtype="int16",
                callback=self.sd_input_audio_callback,
                device=in_dev_index,
                samplerate=self.AUDIO_SAMPLE_RATE,
                blocksize=4800,
            )
            self.sd_input_stream.start()

            self.sd_output_stream = sd.OutputStream(
                channels=1,
                dtype="int16",
                callback=self.sd_output_audio_callback,
                device=out_dev_index,
                samplerate=self.AUDIO_SAMPLE_RATE,
                blocksize=2400,
            )
            self.sd_output_stream.start()

            return True

        except Exception as audioerr:
            self.log.error("[MDM] init: starting pyaudio callback failed", e=audioerr)
            self.stop_modem()
            return False

    def transmit_sine(self):
        """ Transmit a sine wave for audio tuning """
        self.states.setTransmitting(True)
        self.log.info("[MDM] TRANSMIT", mode="SINE")
        start_of_transmission = time.time()

        f0 = 1500  # Frequency of sine wave in Hz
        fs = 48000  # Sample rate in Hz
        max_duration = 30  # Maximum duration in seconds

        # Create sine wave signal
        t = np.linspace(0, max_duration, int(fs * max_duration), endpoint=False)
        s = 0.5 * np.sin(2 * np.pi * f0 * t)
        signal = np.int16(s * 32767)  # Convert to 16-bit integer PCM format

        signal = audio.normalize_audio(signal)

        # Set audio volume and prepare buffer for transmission
        txbuffer_out = audio.set_audio_volume(signal, self.tx_audio_level)

        # Transmit audio
        self.enqueue_audio_out(txbuffer_out)

        end_of_transmission = time.time()
        transmission_time = end_of_transmission - start_of_transmission
        self.states.setTransmitting(False)

        self.log.debug("[MDM] ON AIR TIME", time=transmission_time)

    def stop_sine(self):
        """ Stop transmitting sine wave"""
        # clear audio out queue
        self.audio_out_queue.queue.clear()
        self.states.setTransmitting(False)
        self.log.debug("[MDM] Stopped transmitting sine")

    def transmit_morse(self, repeats, repeat_delay, frames):
        """Transmits Morse code.

        This method transmits the station's callsign as Morse code. It waits
        for any ongoing transmissions to complete, sets the transmitting
        state, generates the Morse code audio signal, normalizes it, and
        enqueues it for output. It logs the transmission mode and on-air
        time. The repeats, repeat_delay, and frames arguments are not
        currently used in this method.

        Args:
            repeats: Currently unused.
            repeat_delay: Currently unused.
            frames: Currently unused.
        """
        self.states.waitForTransmission()
        self.states.setTransmitting(True)
        # if we're transmitting FreeDATA signals, reset channel busy state
        self.log.debug(
            "[MDM] TRANSMIT", mode="MORSE"
        )
        start_of_transmission = time.time()
        txbuffer_out = cw.MorseCodePlayer().text_to_signal(self.config['STATION'].get('mycall'))
        txbuffer_out = audio.normalize_audio(txbuffer_out)
        # transmit audio
        self.enqueue_audio_out(txbuffer_out)

        end_of_transmission = time.time()
        transmission_time = end_of_transmission - start_of_transmission
        self.log.debug("[MDM] ON AIR TIME", time=transmission_time)


    def transmit(
            self, mode, repeats: int, repeat_delay: int, frames: bytearray
    ) -> None:
        """Transmits data using the specified mode and parameters.

        This method transmits data using the given FreeDV mode, number of
        repeats, repeat delay, and frames. It handles synchronization with
        other transmissions, creates the modulated burst, resamples the
        audio, sets the transmit audio level, enqueues the audio for
        output, and logs transmission details.

        Args:
            mode: The FreeDV mode to use for transmission.
            repeats (int): The number of times to repeat the frames.
            repeat_delay (int): The delay between repetitions in milliseconds.
            frames (bytearray): The data frames to transmit.
        """

        self.demodulator.reset_data_sync()
        # Wait for some other thread that might be transmitting
        self.states.waitForTransmission()
        self.states.setTransmitting(True)
        # self.states.channel_busy_event.wait()

        start_of_transmission = time.time()
        txbuffer = self.modulator.create_burst(mode, repeats, repeat_delay, frames)

        # Re-sample back up to 48k (resampler works on np.int16)
        x = np.frombuffer(txbuffer, dtype=np.int16)
        
        if self.config['AUDIO'].get('tx_auto_audio_level'):
            x = audio.normalize_audio(x)
        x = audio.set_audio_volume(x, self.tx_audio_level)
        txbuffer_out = self.resampler.resample8_to_48(x)
        # transmit audio
        self.enqueue_audio_out(txbuffer_out)

        end_of_transmission = time.time()
        transmission_time = end_of_transmission - start_of_transmission
        self.log.debug("[MDM] ON AIR TIME", time=transmission_time)



    def enqueue_audio_out(self, audio_48k) -> None:
        """Enqueues audio data for output.

        This method enqueues the provided 48kHz audio data for output. It
        handles PTT activation, event signaling, slicing the audio into
        blocks, and adding the blocks to the output queue. It also manages
        the transmitting state and waits for the transmission to complete
        before deactivating PTT.

        Args:
            audio_48k (numpy.ndarray): The 48kHz audio data to enqueue.
        """
        self.enqueuing_audio = True
        if not self.states.isTransmitting():
            self.states.setTransmitting(True)

        self.radio.set_ptt(True)

        self.event_manager.send_ptt_change(True)

        # slice audio data to needed blocklength
        block_size = self.sd_output_stream.blocksize
        pad_length = -len(audio_48k) % block_size
        padded_data = np.pad(audio_48k, (0, pad_length), mode='constant')
        sliced_audio_data = padded_data.reshape(-1, block_size)
        # add each block to audio out queue
        for block in sliced_audio_data:
            self.audio_out_queue.put(block)


        self.enqueuing_audio = False
        self.states.transmitting_event.wait()

        self.radio.set_ptt(False)
        self.event_manager.send_ptt_change(False)

        return

    def sd_output_audio_callback(self, outdata: np.ndarray, frames: int, time, status) -> None:
        """Callback function for the audio output stream.

        This method is called by the SoundDevice output stream to provide
        audio data for playback. It retrieves audio chunks from the output
        queue, resamples them to 8kHz, calculates the FFT, and sends the
        data to the output stream. It also manages the transmitting state
        and handles exceptions during audio processing.

        Args:
            outdata (np.ndarray): The output audio buffer.
            frames (int): The number of frames to output.
            time: The current time.
            status: The status of the output stream.
        """

        try:
            if not self.audio_out_queue.empty() and not self.enqueuing_audio:
                chunk = self.audio_out_queue.get_nowait()
                audio_8k = self.resampler.resample48_to_8(chunk)
                audio.calculate_fft(audio_8k, self.fft_queue, self.states)
                outdata[:] = chunk.reshape(outdata.shape)

            else:
                # reset transmitting state only, if we are not actively processing audio
                # for avoiding a ptt toggle state bug
                if self.audio_out_queue.empty() and not self.enqueuing_audio:
                    self.states.setTransmitting(False)
                # Fill with zeros if the queue is empty
                outdata.fill(0)
        except Exception as e:
            self.log.warning("[AUDIO STATUS]", status=status, time=time, frames=frames, e=e)
            outdata.fill(0)

    def sd_input_audio_callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        """Callback function for the audio input stream.

        This method is called by the SoundDevice input stream when audio
        data is available. It resamples the incoming 48kHz audio to 8kHz,
        adjusts the audio level, calculates FFT data if not transmitting,
        and pushes the audio data to the appropriate demodulator buffers.
        It handles buffer overflows and logs audio exceptions.

        Args:
            indata (np.ndarray): Input audio data buffer.
            frames (int): Number of frames received.
            time: Current time.
            status: Input stream status.
        """
        if status:
            self.log.warning("[AUDIO STATUS]", status=status, time=time, frames=frames)
            # FIXME on windows input overflows crashing the rx audio stream. Lets restart the server then
            #if status.input_overflow:
            #    self.service_queue.put("restart")
            return
        try:
            audio_48k = np.frombuffer(indata, dtype=np.int16)
            audio_8k = self.resampler.resample48_to_8(audio_48k)
            if self.config['AUDIO'].get('rx_auto_audio_level'):
                audio_8k = audio.normalize_audio(audio_8k)

            audio_8k_level_adjusted = audio.set_audio_volume(audio_8k, self.rx_audio_level)

            if not self.states.isTransmitting():
                audio.calculate_fft(audio_8k_level_adjusted, self.fft_queue, self.states)

            length_audio_8k_level_adjusted = len(audio_8k_level_adjusted)
            # Avoid buffer overflow by filling only if buffer for
            # selected datachannel mode is not full
            index = 0
            for mode in self.demodulator.MODE_DICT:
                mode_data = self.demodulator.MODE_DICT[mode]
                audiobuffer = mode_data['audio_buffer']
                decode = mode_data['decode']
                index += 1
                if audiobuffer:
                    if (audiobuffer.nbuffer + length_audio_8k_level_adjusted) > audiobuffer.size:
                        self.demodulator.buffer_overflow_counter[index] += 1
                        self.event_manager.send_buffer_overflow(self.demodulator.buffer_overflow_counter)
                    elif decode:
                        audiobuffer.push(audio_8k_level_adjusted)
        except Exception as e:
            self.log.warning("[AUDIO EXCEPTION]", status=status, time=time, frames=frames, e=e)