"""
This module plots the acquired signal.


Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import struct

import numpy as np
from matplotlib import pyplot as plt
from scipy import signal


def main():
    # Input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        required=True,
        type=str,
        help="Path to the .bin file",
    )
    parser.add_argument(
        "--fs",
        required=True,
        type=float,
        help="Sampling frequency",
    )
    parser.add_argument(
        "--filtType",
        required=False,
        type=str,
        help='Filter type ("lowpass", "highpass", "bandpass")',
    )
    parser.add_argument(
        "--f1",
        required=False,
        type=float,
        help="1st cut-off frequency",
    )
    parser.add_argument(
        "--f2",
        required=False,
        type=float,
        help="2nd cut-off frequency",
    )
    parser.add_argument(
        "--trigger",
        action="store_true",
        help="Whether to consider the last channel as trigger",
    )
    args = vars(parser.parse_args())

    filePath = args["path"]
    fs = args["fs"]

    # Read data
    with open(filePath, "rb") as f:
        nCh = struct.unpack("<I", f.read(4))[0]
        bSig = bytes(f.read())
    sig = np.frombuffer(bSig, dtype="float32").reshape(-1, nCh).T
    nSamp = sig.shape[1]

    # Read timestamp
    ts, sig = sig[-1], sig[:-1]
    nCh -= 1

    # Handle trigger
    if args["trigger"]:
        trigger, sig = sig[-1], sig[:-1]
        nCh -= 1

    # Handle filtering
    if args["filtType"]:
        cutOffFreqs = [args["f1"]]
        if args["filtType"] == "bandpass":
            cutOffFreqs.append(args["f2"])
        sos = signal.butter(4, cutOffFreqs, args["filtType"], output="sos", fs=fs)
        sig = signal.sosfiltfilt(sos, sig)

    # Plot
    t = np.arange(nSamp) / fs
    if args["trigger"]:
        _, axes = plt.subplots(
            nrows=nCh + 2, sharex="all", figsize=(16, 20), layout="constrained"
        )
        for i in range(nCh):
            axes[i].plot(t, sig[i])
        axes[-2].set_title("Timestamp")
        axes[-2].plot(t, ts)
        axes[-1].set_title("Trigger")
        axes[-1].plot(t, trigger)
    else:
        _, axes = plt.subplots(
            nrows=nCh + 1, sharex="all", figsize=(16, 20), layout="constrained"
        )
        for i in range(nCh):
            axes[i].plot(t, sig[i])
        axes[-1].set_title("Timestamp")
        axes[-1].plot(t, ts)

    plt.show()


if __name__ == "__main__":
    main()
