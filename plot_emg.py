#!/bin/python

import sys

import numpy as np
from matplotlib import pyplot as plt
from scipy import signal


def main():
    file_path = sys.argv[1]
    with open(file_path, "rb") as f:
        b_sig = bytes(f.read())
    sig = np.frombuffer(b_sig, dtype="float32").reshape(-1, 17)
    trigger = sig[:, -1]
    sig = sig[:, :-1].T

    fs = 4000
    n_ch, n_samp = sig.shape
    t = np.arange(n_samp) / fs

    sos = signal.butter(4, 20, "high", output="sos", fs=fs)
    sig = signal.sosfiltfilt(sos, sig)

    _, axes = plt.subplots(
        nrows=n_ch + 1, sharex="all", figsize=(16, 20), layout="constrained"
    )
    for i in range(n_ch):
        axes[i].plot(t, sig[i])
    axes[-1].set_title("Trigger")
    axes[-1].plot(t, trigger)

    plt.show()


if __name__ == "__main__":
    main()
