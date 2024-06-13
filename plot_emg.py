import struct
import sys

import numpy as np
from matplotlib import pyplot as plt
from scipy import signal


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 plot_emg filePath sampFreq")

    filePath = sys.argv[1]
    fs = int(sys.argv[2])

    # Read data
    with open(filePath, "rb") as f:
        nChAndTrigger = struct.unpack("<I", f.read(4))[0]
        bSig = bytes(f.read())
    sig = np.frombuffer(bSig, dtype="float32").reshape(-1, nChAndTrigger)
    trigger = sig[:, -1]
    sig = sig[:, :-1].T
    nCh, nSamp = sig.shape
    t = np.arange(nSamp) / fs

    # Band-pass filter
    sos = signal.butter(4, (20, 500), "bandpass", output="sos", fs=fs)
    sig = signal.sosfiltfilt(sos, sig)

    # Plot
    _, axes = plt.subplots(
        nrows=nChAndTrigger, sharex="all", figsize=(16, 20), layout="constrained"
    )
    for i in range(nCh):
        axes[i].plot(t, sig[i])
    axes[-1].set_title("Trigger")
    axes[-1].plot(t, trigger)

    plt.show()


if __name__ == "__main__":
    main()
