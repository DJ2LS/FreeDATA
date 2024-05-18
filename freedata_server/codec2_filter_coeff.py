import numpy as np
#from scipy.signal import freqz
import ctypes

testFilter = (ctypes.c_float * 3)(1.000000,1.000000,1.000000)

def generate_filter_coefficients(Fs_Hz, bandwidth_Hz, taps):
    # ported from https://github.com/drowe67/misc/blob/master/radio_ae/rx.py#L73
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