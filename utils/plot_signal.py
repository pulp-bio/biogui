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

import argparse
import struct
import sys

import numpy as np
from matplotlib import pyplot as plt


def read_bio_file(file_path: str) -> dict:
    """
    Read a .bio file and extract all signals, timestamps, and triggers.

    Parameters
    ----------
    file_path : str
        Path to the .bio file.

    Returns
    -------
    dict
        Dictionary with structure:
        {
            'timestamp': {'data': ndarray, 'fs': float},
            'signal_name': {'data': ndarray, 'fs': float},
            ...
            'trigger': {'data': ndarray, 'fs': float}  # if present
        }

        Note: trigger values are stored in signals['trigger']['data']
              NOT as a separate top-level key!
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
            trigger = np.frombuffer(f.read(), dtype=np.uint32).reshape(n_samp_base, 1)
            signals["trigger"] = {"data": trigger, "fs": fs_base}

    return signals


def plot_signal_mmode(
    sig_name: str, sig_data: dict, samples_per_acquisition: int = 400
):
    """
    Plot a single signal in M-mode (time vs depth with intensity as color).

    Parameters
    ----------
    sig_name : str
        Name of the signal.
    sig_data : dict
        Dictionary containing the signal data.
    samples_per_acquisition : int
        Number of samples per acquisition (default: 400).
    """
    data = sig_data["data"]
    fs = sig_data["fs"]
    n_samp, n_ch = data.shape

    # Calculate number of acquisitions
    n_acquisitions = n_samp // samples_per_acquisition

    if n_acquisitions == 0:
        print(
            f"Warning: Signal '{sig_name}' has not enough samples for even one acquisition (need {samples_per_acquisition}, got {n_samp}). Skipping."
        )
        return

    # Reshape data into acquisitions: (n_acquisitions, samples_per_acquisition, n_ch)
    truncated_samples = n_acquisitions * samples_per_acquisition
    data_reshaped = data[:truncated_samples, :].reshape(
        n_acquisitions, samples_per_acquisition, n_ch
    )

    # Time axis: time of each acquisition
    acquisition_duration = samples_per_acquisition / fs
    time_axis = np.arange(n_acquisitions) * acquisition_duration

    # Depth axis: sample index within each acquisition
    depth_axis = np.arange(samples_per_acquisition)

    # Create figure with subplots for each channel
    fig, axes = plt.subplots(
        nrows=n_ch,
        sharex=True,
        figsize=(16, n_ch * 4),
        layout="constrained",
    )

    # Handle single channel case (axes is not a list)
    if n_ch == 1:
        axes = [axes]

    fig.suptitle(f"{sig_name} - M-mode")

    # Plot M-mode for each channel
    for i in range(n_ch):
        # Transpose so depth is on y-axis and time on x-axis
        mmode_data = data_reshaped[
            :, :, i
        ].T  # Shape: (samples_per_acquisition, n_acquisitions)

        # Calculate dynamic level range for better contrast (like in mmode_plot_mode.py)
        data_min = mmode_data.min()
        data_max = mmode_data.max()
        level_range = data_max - data_min if data_max != data_min else 1.0

        # Set vmin and vmax with some margin for better visibility
        vmin = data_min - 0.1 * level_range
        vmax = data_max + 0.1 * level_range

        im = axes[i].imshow(
            mmode_data,
            aspect="auto",
            cmap="viridis",  # Using viridis like in mmode_plot_mode.py
            extent=[time_axis[0], time_axis[-1], depth_axis[-1], depth_axis[0]],
            interpolation="nearest",
            vmin=vmin,
            vmax=vmax,
        )
        axes[i].set_ylabel(f"Channel {i}\nDepth (sample)")
        axes[i].grid(False)

        # Add colorbar
        plt.colorbar(im, ax=axes[i], label="Intensity")

    axes[-1].set_xlabel("Time (s)")


def plot_signal_standard(sig_name: str, sig_data: dict):
    """
    Standard plot for a single signal.

    Parameters
    ----------
    sig_name : str
        Name of the signal.
    sig_data : dict
        Dictionary containing the signal data.
    """
    n_samp, n_ch = sig_data["data"].shape

    t = np.arange(n_samp) / sig_data["fs"]
    fig, axes = plt.subplots(
        nrows=n_ch,
        sharex="all",
        squeeze=False,
        figsize=(16, n_ch),
        layout="constrained",
    )
    fig.suptitle(sig_name)
    for i in range(n_ch):
        axes[i][0].plot(t, sig_data["data"][:, i])


def plot_ultrasound_mmode(signals: dict, samples_per_acquisition: int = 400):
    """
    Plot ultrasound signals in M-mode, and timestamp/trigger in standard mode.

    Parameters
    ----------
    signals : dict
        Dictionary containing the signal data.
    samples_per_acquisition : int
        Number of samples per acquisition (default: 400).
    """
    # Plot data signals in M-mode
    data_signal_count = 0
    for sig_name, sig_data in signals.items():
        if sig_name not in ["timestamp", "trigger"]:
            plot_signal_mmode(sig_name, sig_data, samples_per_acquisition)
            data_signal_count += 1

    if data_signal_count == 0:
        sys.exit("Error: No data signals found in the file (only timestamp/trigger).")

    # Plot timestamp and trigger in standard mode
    for sig_name, sig_data in signals.items():
        if sig_name in ["timestamp", "trigger"]:
            plot_signal_standard(sig_name, sig_data)

    plt.show()


def plot_standard(signals: dict):
    """
    Standard plot for all signals.

    Parameters
    ----------
    signals : dict
        Dictionary containing the signal data.
    """
    for sig_name, sig_data in signals.items():
        plot_signal_standard(sig_name, sig_data)

    plt.show()


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Plot signals from .bio files")
    parser.add_argument("file_path", type=str, help="Path to the .bio file")
    parser.add_argument(
        "--ultrasound",
        action="store_true",
        help="Display ultrasound data in M-mode (time vs depth)",
    )
    parser.add_argument(
        "--samples-per-acquisition",
        type=int,
        default=400,
        help="Number of samples per acquisition for M-mode (default: 400)",
    )

    args = parser.parse_args()

    # Read signals
    signals = read_bio_file(args.file_path)

    # Plot based on mode
    if args.ultrasound:
        plot_ultrasound_mmode(signals, args.samples_per_acquisition)
    else:
        plot_standard(signals)


if __name__ == "__main__":
    main()
