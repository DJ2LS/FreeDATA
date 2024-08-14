import numpy as np
import sounddevice as sd
from reedsolo import RSCodec
import time
import threading

class MFSKModem:
    def __init__(self, fs=48000, baud_rate=25, num_tones=4, tone_spacing=200, center_frequency=1500, rs_ratio=0.7, doppler_shift_range=10, expected_data_len=32):
        self.fs = fs  # Sampling frequency
        self.baud_rate = baud_rate  # Baud rate (symbols per second)
        self.num_tones = num_tones  # Number of different tones (frequencies)
        self.bits_per_symbol = int(np.log2(num_tones))  # Bits per symbol
        self.center_frequency = center_frequency  # Center frequency for the MFSK tones
        self.guard_band = 100  # Hz
        self.tone_spacing = tone_spacing
        self.buffer = np.array([])  # Internal buffer to store incoming data
        self.buffer_lock = threading.Lock()  # Lock to manage buffer access
        self.decoding_thread = None
        self.running = False  # To control the thread's running state
        self.expected_data_len = expected_data_len
        self.min_energy_treshold = 50
        self.rs_ratio = rs_ratio  # Ratio of data to total codeword length
        # Store rs_n and rs_k for later decoding
        self.rs_n, self.rs_k = self.calculate_rs_parameters(self.expected_data_len)
        self.rs = RSCodec(self.rs_n - self.rs_k)


        self.doppler_shift_range = doppler_shift_range  # Maximum Doppler shift in Hz

        # Define the frequencies for each tone relative to the center frequency
        self.tone_frequencies = np.linspace(
            center_frequency - (self.tone_spacing * (num_tones - 1)) / 2,
            center_frequency + (self.tone_spacing * (num_tones - 1)) / 2,
            num_tones
        )

        self.symbol_duration = 1 / baud_rate  # Duration of each symbol
        self.symbol_length = int(self.fs * self.symbol_duration)  # Number of samples per symbol

    def start_decoding_thread(self):
        """Start the decoding thread."""
        if not self.running:
            self.running = True
            self.decoding_thread = threading.Thread(target=self.decode_in_thread)
            self.decoding_thread.start()

    def stop_decoding_thread(self):
        """Stop the decoding thread."""
        self.running = False
        if self.decoding_thread is not None:
            self.decoding_thread.join()

    def decode_in_thread(self, timeout_seconds: float = 2.0):
        window_step = int(self.symbol_length * 0.5)  # Increase overlap by reducing step size
        detected_symbols = []
        collected_snrs = []  # List to store SNRs for valid symbols
        last_symbol_time = time.time()

        while self.running:
            with self.buffer_lock:
                while len(self.buffer) >= self.symbol_length + window_step:
                    signal_chunk = self.buffer[:self.symbol_length]
                    self.buffer = self.buffer[window_step:]

                    # Detect symbol
                    if self.detect_symbol_start(signal_chunk):
                        detected_symbol, snr_db = self.decode(signal_chunk)
                        if detected_symbol is not None:
                            detected_symbols.append(detected_symbol)
                            collected_snrs.append(snr_db)
                            last_symbol_time = time.time()  # Reset the timeout timer

                # Timeout check
                if time.time() - last_symbol_time > timeout_seconds:
                    print(f"No valid symbols decoded for {timeout_seconds} seconds. Resetting detected symbols.")
                    detected_symbols = []  # Clear detected symbols
                    collected_snrs = []  # Clear SNRs
                    last_symbol_time = time.time()

                # If valid symbols have been detected, process them
                if detected_symbols:
                    self.process_detected_symbols(detected_symbols, collected_snrs)

    def process_detected_symbols(self, detected_symbols, collected_snrs):
        if len(detected_symbols) < 10:  # Ensure sufficient symbols have been detected
            return

        detected_bits = []
        for symbol in detected_symbols:
            bits = [int(bit) for bit in np.binary_repr(symbol, width=self.bits_per_symbol)]
            detected_bits.extend(bits)

        detected_bits = np.array(detected_bits, dtype=np.uint8)
        byte_data = np.packbits(detected_bits)

        # Try Reed-Solomon decoding with slight shifts in byte_data
        for start_index in range(len(byte_data)):
            try:
                potential_data = bytearray(byte_data[start_index:])
                decoded_data = self.rs.decode(potential_data)
                if isinstance(decoded_data, tuple):
                    decoded_data = decoded_data[0][:self.expected_data_len]

                # Calculate average SNR
                avg_snr_db = np.mean(collected_snrs) if collected_snrs else None

                if decoded_data not in [b'', bytearray(b'')]:
                    print(f"Decoded Data: {decoded_data}, Average SNR: {avg_snr_db:.2f} dB")
                    return  # Exit after successful decoding

            except Exception:
                continue  # Try the next start index if decoding fails

        print("Reed-Solomon decoding failed for all attempted start indices.")

    def add_audio_to_buffer(self, audio_48k: np.ndarray):
        """Append incoming audio data to the buffer in a thread-safe manner."""
        # Convert int16 audio data to float32
        audio_float32 = audio_48k.astype(np.float32) / 32767.0  # Normalize to range [-1, 1]

        with self.buffer_lock:  # Using 'with' ensures the lock is released properly
            self.buffer = np.concatenate((self.buffer, audio_float32))  # Append incoming data to the buffer

    def calculate_rs_parameters(self, data_length):
        """Calculate the RS(n, k) parameters based on the input data length and the specified ratio."""
        max_n = 255  # Maximum value for n in RS(255, k) on GF(2^8)

        # Calculate k and n based on the input data length and ratio
        rs_k = min(max_n, data_length)
        rs_n = int(rs_k / self.rs_ratio)

        # Ensure n doesn't exceed max_n
        rs_n = min(max_n, rs_n)

        # Adjust k accordingly
        rs_k = int(rs_n * self.rs_ratio)

        return rs_n, rs_k

    def calculate_bandwidth(self):
        """Calculate the occupied bandwidth of the MFSK signal."""
        # Bandwidth without guard band
        bandwidth = (self.num_tones - 1) * self.tone_spacing

        # Add guard bands
        total_bandwidth = bandwidth + 2 * self.guard_band

        return total_bandwidth

    def encode(self, data: bytes) -> np.ndarray:
        """Encode a bytearray into an MFSK signal with Reed-Solomon FEC."""
        rs_encoded_data = self.rs.encode(data)

        # Convert bytearray to binary data
        binary_data = np.unpackbits(np.array(bytearray(rs_encoded_data), dtype=np.uint8))

        # Pad binary data to make its length a multiple of bits_per_symbol
        padding_length = (self.bits_per_symbol - len(binary_data) % self.bits_per_symbol) % self.bits_per_symbol
        binary_data = np.pad(binary_data, (0, padding_length), 'constant')

        # Group binary data into symbols
        symbols = []
        for i in range(0, len(binary_data), self.bits_per_symbol):
            symbol = 0
            for b in range(self.bits_per_symbol):
                symbol += binary_data[i + b] * (2 ** (self.bits_per_symbol - 1 - b))
            symbols.append(symbol)
        symbols = np.array(symbols)
        print(symbols)

        # Generate the MFSK signal
        t = np.linspace(0, self.symbol_duration, self.symbol_length, endpoint=False)
        signal = np.concatenate([np.sin(2 * np.pi * self.tone_frequencies[sym] * t) for sym in symbols])

        # Normalize the signal to the range of int16
        signal = signal / np.max(np.abs(signal))  # Normalize to range [-1, 1]
        signal = np.int16(signal * 32767)  # Scale to int16 range [-32767, 32767]

        return signal

    def decode(self, signal_chunk: np.ndarray) -> tuple:
        """Decode a single chunk of MFSK signal into a symbol and calculate its SNR."""
        t = np.linspace(0, self.symbol_duration, self.symbol_length, endpoint=False)

        if len(signal_chunk) != self.symbol_length:
            raise ValueError(f"Expected signal_chunk of length {self.symbol_length}, but got {len(signal_chunk)}")

        best_symbol = None
        max_energy = -np.inf

        # Check each tone frequency with a small range of frequency offsets to account for Doppler shift
        for tone_index, tone_freq in enumerate(self.tone_frequencies):
            # Generate the frequency range to check
            for freq_offset in np.linspace(-self.doppler_shift_range, self.doppler_shift_range, num=10):
                adjusted_frequency = tone_freq + freq_offset
                energy = np.sum(np.sin(2 * np.pi * adjusted_frequency * t) * signal_chunk)

                if energy > max_energy:
                    max_energy = energy
                    best_symbol = tone_index

        # Check if the best symbol's energy exceeds a certain threshold to be considered valid
        if max_energy > self.min_energy_treshold:
            snr_db = self.calculate_snr(signal_chunk)  # Calculate SNR only for valid symbols
            return best_symbol, snr_db
        else:
            return None, None

    def decode_in_thread(self, timeout_seconds: float = 1.0):
        window_step = int(self.symbol_length * 1)  # Smaller step for better overlap detection
        detected_symbols = []
        collected_snrs = []  # List to store SNRs for valid symbols
        last_symbol_time = time.time()
        min_symbol_energy = 0.01  # Threshold to detect the start of a symbol (tune this value)

        self.rs = RSCodec(self.rs_n - self.rs_k)

        while self.running:
            self.buffer_lock.acquire()

            # Process while there's enough data in the buffer
            while len(self.buffer) >= self.symbol_length + window_step:
                signal_chunk = self.buffer[:self.symbol_length]
                # Perform start-of-symbol detection
                if self.detect_symbol_start(signal_chunk, min_symbol_energy):
                    # Decode the detected symbol
                    detected_symbol, snr_db = self.decode(signal_chunk)
                    if detected_symbol is not None:
                        detected_symbols.append(detected_symbol)
                        collected_snrs.append(snr_db)  # Collect the SNR
                        last_symbol_time = time.time()  # Reset the timeout timer

                # Slide the window over the buffer
                self.buffer = self.buffer[window_step:]
                self.buffer_lock.release()

                # Reacquire the lock for the next iteration
                self.buffer_lock.acquire()

            self.buffer_lock.release()
            threading.Event().wait(0.01)

            # Timeout check: clear detected symbols if no valid symbols are decoded within the timeout period
            if time.time() - last_symbol_time > timeout_seconds:
                print(f"No valid symbols decoded for {timeout_seconds} seconds. Resetting detected symbols.")
                detected_symbols = []  # Clear detected symbols
                collected_snrs = []  # Clear SNRs
                last_symbol_time = time.time()

            # If valid symbols have been detected, process them
            if detected_symbols:
                self.process_detected_symbols(detected_symbols, collected_snrs, signal_chunk)

    def process_detected_symbols(self, detected_symbols, collected_snrs, signal_chunk):
        """Process and decode detected symbols into bytes, and calculate summary SNR."""
        detected_bits = []
        if len(detected_symbols) <= 10:
            return

        for symbol in detected_symbols:
            bits = [int(bit) for bit in np.binary_repr(symbol, width=self.bits_per_symbol)]
            detected_bits.extend(bits)

        # Ensure bits length is a multiple of 8 for byte packing
        detected_bits = np.array(detected_bits, dtype=np.uint8)
        byte_data = np.packbits(detected_bits)

        # Calculate the average SNR for all collected symbols
        if collected_snrs:
            avg_snr_db = np.mean(collected_snrs)
            print(collected_snrs)
        else:
            avg_snr_db = None

        # Iterate through byte_data to search for valid Reed-Solomon decoding
        decoded_data = None
        for start_index in range(len(byte_data)):
            try:
                potential_data = bytearray(byte_data[start_index:])
                decoded_data = self.rs.decode(potential_data)
                if isinstance(decoded_data, tuple):
                    decoded_data = decoded_data[0][:self.expected_data_len]

                # If decoding is successful, print the decoded data and average SNR
                print(f"Detected Symbols: {detected_symbols}")
                print(f"Decoded Data: {decoded_data}, Average SNR: {avg_snr_db:.2f} dB")
                return  # Exit after successful decoding

            except Exception as e:
                # Continue trying other start indices if decoding fails
                continue

        # If no valid data found
        if decoded_data is None:
            print("Reed-Solomon decoding failed for all attempted start indices.")

    def detect_symbol_start(self, signal_chunk: np.ndarray, min_symbol_energy: float) -> bool:
        """Detect if the current chunk contains the start of a symbol."""
        energy = np.sum(np.abs(signal_chunk) ** 2) / len(signal_chunk)
        return energy > min_symbol_energy  # Return True if the energy indicates a likely start of a symbol


        # Iterate through byte_data to search for valid Reed-Solomon decoding
        decoded_data = None
        for start_index in range(len(byte_data)):
            try:
                potential_data = bytearray(byte_data[start_index:])
                decoded_data = self.rs.decode(potential_data)
                if isinstance(decoded_data, tuple):
                    decoded_data = decoded_data[0][:self.expected_data_len]

                # If decoding is successful, calculate SNR and print the decoded data
                snr_db = self.calculate_snr(signal_chunk)
                print(detected_symbols)
                print(f"Decoded Data: {decoded_data}, SNR: {snr_db}")
                return  # Exit after successful decoding

            except Exception as e:
                # Continue trying other start indices if decoding fails
                continue

        # If no valid data found
        if decoded_data is None:
            print("Reed-Solomon decoding failed for all attempted start indices.")

    def calculate_snr(self, signal: np.ndarray) -> float:
        """Calculate the Signal-to-Noise Ratio (SNR) of a given signal."""
        t = np.linspace(0, self.symbol_duration, self.symbol_length, endpoint=False)
        reconstructed_signal = np.zeros_like(signal)

        # Reconstruct the signal using the strongest tone
        for i in range(0, len(signal), self.symbol_length):
            symbol_chunk = signal[i:i + self.symbol_length]
            energies = [np.sum(np.sin(2 * np.pi * f * t) * symbol_chunk) for f in self.tone_frequencies]
            strongest_tone_index = np.argmax(energies)
            reconstructed_signal[i:i + self.symbol_length] = np.sin(
                2 * np.pi * self.tone_frequencies[strongest_tone_index] * t)

        # Calculate the noise as the difference between the original signal and the reconstructed signal
        noise = signal - reconstructed_signal

        # Calculate power of the signal and the noise
        signal_power = np.mean(np.abs(reconstructed_signal) ** 2)
        noise_power = np.mean(np.abs(noise) ** 2)

        # Calculate SNR in dB
        snr_linear = signal_power / noise_power
        snr_db = 10 * np.log10(snr_linear)

        return snr_db

    def play_signal(self, signal: np.ndarray):
        """Play the MFSK signal through the sound device."""
        # Convert the signal to real values if it's complex
        signal_real = np.real(signal)
        # Convert the signal to int16 format
        signal_int16 = np.int16(signal_real / np.max(np.abs(signal_real)) * 32767)
        sd.play(signal_int16, self.fs)
        sd.wait()

    def plot_all(self, original_signal: np.ndarray, simulated_signal: np.ndarray, symbols: list):
        """Plot the original signal, simulated signal, spectrogram, and detected symbols in one big plot."""
        fig, axs = plt.subplots(4, 1, figsize=(12, 16))

        # Plot original signal
        axs[0].plot(original_signal[:1000])
        axs[0].set_title('Original MFSK Signal')
        axs[0].set_xlabel('Sample')
        axs[0].set_ylabel('Amplitude')
        axs[0].grid(True)

        # Plot simulated signal
        axs[1].plot(simulated_signal[:1000])
        axs[1].set_title('Simulated HF Channel Signal')
        axs[1].set_xlabel('Sample')
        axs[1].set_ylabel('Amplitude')
        axs[1].grid(True)

        # Plot spectrogram of simulated signal
        spec, freqs, bins, im = axs[2].specgram(simulated_signal, NFFT=1024, Fs=self.fs, noverlap=512, cmap='viridis')
        axs[2].set_title('Simulated HF Channel Signal Spectrogram')
        axs[2].set_xlabel('Time [s]')
        axs[2].set_ylabel('Frequency [Hz]')
        fig.colorbar(im, ax=axs[2], label='Intensity [dB]')

        # Limit the y-axis to the bandwidth of interest
        axs[2].set_ylim(min(self.tone_frequencies) - 100, max(self.tone_frequencies) + 100)


        # Plot detected symbols
        axs[3].plot(symbols, marker='o')
        axs[3].set_title('Detected Symbols')
        axs[3].set_xlabel('Symbol Index')
        axs[3].set_ylabel('Symbol Value')
        axs[3].grid(True)

        plt.tight_layout()
        plt.show()


class HFChannelSimulator:
    def __init__(self, fs=48000, time_delay=0.5e-3, freq_spread=0.1, doppler_shift=0, snr_db=20, awgn_only=False):
        self.fs = fs  # Sampling frequency
        self.time_delay = time_delay  # Differential time delay in seconds
        self.freq_spread = freq_spread  # Frequency spread in Hz
        self.doppler_shift = doppler_shift  # Doppler shift in Hz
        self.snr_db = snr_db  # Signal-to-noise ratio in dB
        self.awgn_only = awgn_only  # If true, apply only AWGN without HF effects

    def apply_multipath(self, signal):
        """Apply multipath effect with a differential time delay."""
        delay_samples = int(self.time_delay * self.fs)
        delayed_signal = np.roll(signal, delay_samples) * np.exp(
            2j * np.pi * self.freq_spread * np.arange(len(signal)) / self.fs)
        multipath_signal = signal + delayed_signal
        return multipath_signal

    def apply_doppler_shift(self, signal):
        """Apply Doppler shift to the signal."""
        time = np.arange(len(signal)) / self.fs
        doppler_effect = np.exp(2j * np.pi * self.doppler_shift * time)
        return signal * doppler_effect

    def apply_awgn(self, signal):
        """Add AWGN noise to the signal."""
        signal_power = np.mean(np.abs(signal) ** 2)
        snr_linear = 10 ** (self.snr_db / 10.0)
        noise_power = signal_power / snr_linear
        noise = np.sqrt(noise_power) * np.random.normal(size=len(signal))
        return signal + noise

    def simulate(self, signal):
        """Simulate the HF channel effects on the signal, or apply only AWGN if awgn_only is True."""
        if not self.awgn_only:
            # Apply HF effects
            signal = self.apply_multipath(signal)
            if self.doppler_shift != 0:
                signal = self.apply_doppler_shift(signal)

        # Apply AWGN noise
        signal = self.apply_awgn(signal)

        return signal



"""


# Example scenarios with SNR values
def create_simulation_scenario(name, time_delay=None, freq_spread=None, doppler_shift=0, snr_db=20, awgn_only=False):
    print(f"Running simulation for: {name} with SNR {snr_db} dB")
    return HFChannelSimulator(time_delay=time_delay, freq_spread=freq_spread, doppler_shift=doppler_shift, snr_db=snr_db, awgn_only=awgn_only)

# Good conditions with specific SNR
good_conditions = create_simulation_scenario("Good Conditions", time_delay=0.5e-3, freq_spread=0.1, snr_db=-15)

# Moderate conditions with specific SNR
moderate_conditions = create_simulation_scenario("Moderate Conditions", time_delay=1e-3, freq_spread=0.5, snr_db=-15)

# Poor conditions with specific SNR
poor_conditions = create_simulation_scenario("Poor Conditions", time_delay=2e-3, freq_spread=1.0, snr_db=-15)

# Flutter fading with specific SNR
flutter_fading = create_simulation_scenario("Flutter Fading", time_delay=0.5e-3, freq_spread=10, snr_db=-15)

# Doppler, multipath, and fading with specific SNR
doppler_multipath_fading = create_simulation_scenario("Doppler, Multipath, and Fading", time_delay=0.5e-3, freq_spread=0.2, doppler_shift=5, snr_db=-10)

# AWGN channel only with specific SNR
awgn_only = create_simulation_scenario("AWGN Only", snr_db=-20, awgn_only=True)



data = b'test!'

#mfsk_instance = MFSKModem(fs=48000, baud_rate=75, num_tones=8, tone_spacing=100, center_frequency=1500, rs_ratio=0.5) # 900Hz, working at -15dB MPG, ca 2.5s (16Bytes)
#mfsk_instance = MFSKModem(fs=48000, baud_rate=75, num_tones=4, tone_spacing=100, center_frequency=1500, rs_ratio=0.5) # 500Hz, working at -15dB MPG, ca 4s (16Bytes)
#mfsk_instance = MFSKModem(fs=48000, baud_rate=50, num_tones=4, tone_spacing=100, center_frequency=1500, rs_ratio=0.5, expected_data_len=len(data)) # 500Hz, working at -15dB MPG, ca 2.5s (16Bytes)
mfsk_instance = MFSKModem(fs=48000, baud_rate=20, num_tones=4, tone_spacing=100, center_frequency=1500, rs_ratio=0.5, expected_data_len=len(data)) # 500Hz, working at -15dB MPG, ca 2.5s (16Bytes)

mfsk_instance.start_decoding_thread()

encoded_signal = mfsk_instance.encode(data)

print(f"The calculated bandwidth of the MFSK modem is {mfsk_instance.calculate_bandwidth()} Hz")

# Simulate HF channel effects
simulated_signal_hf = poor_conditions.simulate(encoded_signal)
simulated_signal_awgn = awgn_only.simulate(encoded_signal)

mfsk_instance.play_signal(simulated_signal_hf)
mfsk_instance.add_audio_to_buffer(simulated_signal_hf)

"""


"""
# Decode and print SNR for HF channel
decoded_data_hf, snr_db_hf = mfsk_instance.decode_from_stream(np.real(simulated_signal_hf))
print(f"HF Channel -> Decoded message: {decoded_data_hf.decode('utf-8')}, SNR: {snr_db_hf:.2f} dB")

# Decode and print SNR for AWGN channel
decoded_data_awgn, snr_db_awgn = mfsk_instance.decode_from_stream(np.real(simulated_signal_awgn))
print(f"AWGN Channel -> Decoded message: {decoded_data_awgn.decode('utf-8')}, SNR: {snr_db_awgn:.2f} dB")

# Extract symbols from the decoded data for plotting purposes
symbols_hf = mfsk_instance.decode_from_stream(np.real(simulated_signal_hf))[0]
mfsk_instance.plot_all(original_signal=encoded_signal, simulated_signal=simulated_signal_hf, symbols=symbols_hf)

symbols_awgn = mfsk_instance.decode_from_stream(np.real(simulated_signal_awgn))[0]
mfsk_instance.plot_all(original_signal=encoded_signal, simulated_signal=simulated_signal_awgn, symbols=symbols_awgn)
"""