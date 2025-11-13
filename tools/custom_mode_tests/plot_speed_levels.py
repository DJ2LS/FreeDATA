import matplotlib.pyplot as plt
import numpy as np

codec2_modes = {
    "datac4": {
        "min_snr": -4,
        "bit_rate": 87,  # Bit rate in bits per second
        "bandwidth": 250,  # Bandwidth in Hz
    },
    "data_ofdm_500": {
        "min_snr": 1,
        "bit_rate": 276,
        "bandwidth": 500,
    },
    "datac1": {
        "min_snr": 5,
        "bit_rate": 980,
        "bandwidth": 1700,
    },
    #'datac2000': {
    #    'min_snr': 7.5,
    #    'bit_rate': 1280,
    #    'bandwidth': 2000,
    # },
    "data_ofdm_2438": {
        "min_snr": 8.5,
        "bit_rate": 1830,
        "bandwidth": 2438,
    },
}


# Extracting data from the dictionary
snr_values = [info["min_snr"] for info in codec2_modes.values()]
bit_rates = [info["bit_rate"] for info in codec2_modes.values()]
bandwidths = [info["bandwidth"] for info in codec2_modes.values()]
modes = list(codec2_modes.keys())  # Get the mode names


# Plot bit/s vs SNR
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.scatter(snr_values, bit_rates, color="b")
for i, txt in enumerate(modes):
    plt.annotate(txt, (snr_values[i], bit_rates[i]))  # Annotate each point with mode name
plt.plot(snr_values, bit_rates, "--", color="b")

plt.yscale("log")

plt.xlabel("SNR (dB)")
plt.ylabel("Bit/s")
plt.title("Bit Rate vs SNR")
plt.grid(True)

# Plot bandwidth vs SNR
plt.subplot(1, 2, 2)
plt.scatter(snr_values, bandwidths, color="g")
for i, txt in enumerate(modes):
    plt.annotate(txt, (snr_values[i], bandwidths[i]))  # Annotate each point with mode name
plt.plot(snr_values, bandwidths, "--", color="g")
plt.xlabel("SNR (dB)")
plt.ylabel("Bandwidth (Hz)")
plt.title("Bandwidth vs SNR")
plt.grid(True)

# Show plot
plt.tight_layout()
plt.show()
