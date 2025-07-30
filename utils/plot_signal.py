"""
This script reads the .bio file and plots the acquired signal.


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

import struct
import sys

import numpy as np
from matplotlib import pyplot as plt

from scipy.signal import butter, filtfilt
#define butter lowpass filter
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

# Define the bandpass filter
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

# Apply the bandpass filter
def bandpass_filter(data, lowcut, highcut, fs, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data, axis=0)
    return y

#apply the lowpass filter   
def lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)  
    y = filtfilt(b, a, data, axis=0)
    return y
#define notch filter
def notch_filter(data, fs, f0, Q):
    nyq = 0.5 * fs
    low = f0 - (f0 / Q)
    high = f0 + (f0 / Q)
    b, a = butter(2, [low / nyq, high / nyq], btype='bandstop')
    y = filtfilt(b, a, data, axis=0)
    return y

def decode_trigger(trigger_value):
    sentence_index = (trigger_value // 1000) - 1
    repetition = (trigger_value % 1000) // 10
    is_voiced = (trigger_value % 10) == 1
    return sentence_index, repetition, is_voiced

def read_bio_file(file_path: str) -> dict:
    """
    Parameters
    ----------
    file_path : str
        Path to the .bio file.

    Returns
    -------
    dict
        Dictionary containing timestamp, signals and trigger.
    """
    dtypeMap = {
        "?": np.dtype("bool"),
        "b": np.dtype("int8"),
        "B": np.dtype("uint8"),
        "h": np.dtype("int16"),
        "H": np.dtype("uint16"),
        "i": np.dtype("int32"),
        "I": np.dtype("uint32"),
        "q": np.dtype("int64"),
        "Q": np.dtype("uint64"),
        "f": np.dtype("float32"),
        "d": np.dtype("float64"),
    }

    # Read data
    with open(file_path, "rb") as f:
        # Read number of signals
        n_signals = struct.unpack("<I", f.read(4))[0]

        # Read other metadata
        fs_base, n_samp_base = struct.unpack("<fI", f.read(8))
        signals = {}
        for _ in range(n_signals):
            sig_name_len = struct.unpack("<I", f.read(4))[0]
            sig_name = struct.unpack(f"<{sig_name_len}s", f.read(sig_name_len))[
                0
            ].decode()
            fs, n_samp, n_ch, dtype = struct.unpack("<f2Ic", f.read(13))
            dtype = dtypeMap[dtype.decode("ascii")]

            # Initialize signal array
            signals[sig_name] = {
                "fs": fs,
                "n_samp": n_samp,
                "n_ch": n_ch,
                "dtype": dtype,
            }

        # Read whether the trigger is available
        is_trigger = struct.unpack("<?", f.read(1))[0]

        # Read actual signals:
        # 1. Timestamp
        ts = np.frombuffer(f.read(8 * n_samp_base), dtype=np.float64).reshape(
            n_samp_base, 1
        )
        signals["timestamp"] = {"data": ts, "fs": fs_base}

        # 2. Signals data
        for sig_name, sig_data in signals.items():
            if sig_name == "timestamp":
                continue

            n_samp = sig_data.pop("n_samp")
            n_ch = sig_data.pop("n_ch")
            dtype = sig_data.pop("dtype")
            data = np.frombuffer(
                f.read(dtype.itemsize * n_samp * n_ch), dtype=dtype
            ).reshape(n_samp, n_ch)
            sig_data["data"] = data

        # 3. Trigger (optional)
        if is_trigger:
            trigger = np.frombuffer(f.read(), dtype=np.int32).reshape(n_samp_base, 1)

            signals["trigger"] = {"data": trigger, "fs": fs_base}

    return signals


def main():
    # Input
    if len(sys.argv) != 2:
        sys.exit("Usage: python plot_signal.py PATH_TO_FILE")
    file_path = sys.argv[1]

    signals = read_bio_file(file_path)
    # print(signals["audio"]["data"].shape[0]/signals["audio"]["fs"])s
    if "emg" in signals:
        signals["emg"]["data"] = signals["emg"]["data"][int(10*signals["emg"]["fs"]):int(70*signals["emg"]["fs"]),:9]*3/12*1000
        signals["emg"]["data"] = notch_filter(signals["emg"]["data"], signals["emg"]["fs"], 60, 30)
        signals["emg"]["data"] = bandpass_filter(signals["emg"]["data"], 30, 500, signals["emg"]["fs"], order=4)
    #decode trigger for every samp in the trigger signal using list comprehension and lambda
    if "trigger" in signals:    
        signals["trigger"]["data"] = np.array(
            list(
                map(
                    lambda x: decode_trigger(x[0]),
                    signals["trigger"]["data"],
                )
            )
        )
        # Unpack the decoded trigger values
        sentence_index, repetition, is_voiced = zip(*signals["trigger"]["data"])

    t = np.arange(len(sentence_index)) / signals["trigger"]["fs"]
    print(f"Sentence index: {sentence_index}, Repetition: {repetition}, Is voiced: {is_voiced}")
    #plot sentence index, repetition and is voiced
    plt.figure(figsize=(10, 5))
    plt.plot(t, sentence_index, label="Sentence Index")
    plt.plot(t, repetition, label="Repetition")
    plt.plot(t, is_voiced, label="Is Voiced")
    plt.xlabel("Time [s]")  
    plt.ylabel("Value")
    plt.title("Trigger Signal Decoding")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plot
    for sig_name, sig_data in signals.items():
        #if sig name is emg set the y axis label to microvolts


        n_samp, n_ch = sig_data["data"].shape

        t = np.arange(n_samp) / sig_data["fs"]
        fig, axes = plt.subplots(
            nrows=n_ch,
            sharex="all",
            squeeze=False,
            figsize=(16, n_ch),
            layout="constrained",
            tight_layout=True,
        )
        fig.suptitle(sig_name)
        if sig_name == "emg":
            # set one shared y axis label for all subplots
            for ax in axes[:, 0]:
                ax.set_ylabel("Amplitude [µV]")
                ax.set_xlabel("Time [s]")



        for i in range(n_ch):
            axes[i][0].plot(t, sig_data["data"][:, i])

    plt.show()


if __name__ == "__main__":
    main()
