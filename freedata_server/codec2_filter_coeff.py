import numpy as np
#from scipy.signal import freqz
import ctypes

testFilter = (ctypes.c_float * 3)(1.000000,1.000000,1.000000)

def generate_filter_coefficients(Fs_Hz, bandwidth_Hz, taps):
    """Generates filter coefficients for a sinc filter.

    This function calculates the coefficients for a sinc filter based on the
    provided sampling frequency, bandwidth, and number of taps. The
    coefficients are returned as a ctypes array of floats, with real and
    imaginary parts interleaved.

    Args:
        Fs_Hz (float): The sampling frequency in Hz.
        bandwidth_Hz (float): The bandwidth of the filter in Hz.
        taps (int): The number of taps for the filter.

    Returns:
        ctypes.c_float array: The filter coefficients as a ctypes array.
    """
    B = bandwidth_Hz / Fs_Hz
    Ntap = taps
    h = np.zeros(Ntap, dtype=np.csingle)

    # Generating filter coefficients
    for i in range(Ntap):
        n = i - (Ntap - 1) / 2
        h[i] = B * np.sinc(n * B)

    # Convert to ctypes array (interleaved real and imaginary)
    CArrayType = ctypes.c_float * (len(h) * 2)
    return CArrayType(*(np.hstack([np.real(h), np.imag(h)]).tolist()))

"""
def plot_filter():

    Fs = 8000  # Sampling frequency
    bandwidth = 2438  # Bandwidth in Hz
    centre_freq = 1500  # Centre frequency in Hz

    # Generate filter coefficients
    h = generate_filter_coefficients(Fs, bandwidth, centre_freq)
    print(h)

    # Frequency response
    w, H = freqz(h, worN=8000, fs=Fs)

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(w, 20 * np.log10(np.abs(H)), 'b')
    plt.title('Frequency Response')
    plt.ylabel('Magnitude [dB]')
    plt.grid(True)
    plt.show()

"""