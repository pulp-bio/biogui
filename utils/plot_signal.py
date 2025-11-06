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
from matplotlib.widgets import Slider


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


def plot_signal_amode(
    sig_name: str, sig_data: dict, samples_per_acquisition: int = 400
):
    """
    Plot a single signal in A-mode with a slider to navigate through acquisitions.

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

    # Reshape data into acquisitions
    truncated_samples = n_acquisitions * samples_per_acquisition
    data_reshaped = data[:truncated_samples, :].reshape(
        n_acquisitions, samples_per_acquisition, n_ch
    )

    # Time axis for one acquisition
    t = np.arange(samples_per_acquisition) / fs

    # Create figure with subplots for each channel
    fig, axes = plt.subplots(
        nrows=n_ch,
        sharex=True,
        squeeze=False,
        figsize=(16, n_ch * 3),
    )
    fig.subplots_adjust(bottom=0.15)
    fig.suptitle(f"{sig_name} - A-mode (Acquisition 1/{n_acquisitions})")

    # Initialize plots for each channel
    lines = []
    for i in range(n_ch):
        (line,) = axes[i][0].plot(t, data_reshaped[0, :, i])
        axes[i][0].set_ylabel(f"Channel {i}")
        axes[i][0].grid(True)
        lines.append(line)

    axes[-1][0].set_xlabel("Time (s)")

    # Create slider
    ax_slider = fig.add_axes([0.2, 0.05, 0.6, 0.03])
    slider = Slider(ax_slider, "Acquisition", 1, n_acquisitions, valinit=1, valstep=1)

    # Update function for slider
    def update(val):
        acq_idx = int(slider.val) - 1
        for i in range(n_ch):
            lines[i].set_ydata(data_reshaped[acq_idx, :, i])
        fig.suptitle(
            f"{sig_name} - A-mode (Acquisition {acq_idx + 1}/{n_acquisitions})"
        )
        fig.canvas.draw_idle()

    slider.on_changed(update)


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


def plot_ultrasound_amode(signals: dict, samples_per_acquisition: int = 400):
    """
    Plot ultrasound signals in A-mode with sliders, and timestamp/trigger in standard mode.

    Parameters
    ----------
    signals : dict
        Dictionary containing the signal data.
    samples_per_acquisition : int
        Number of samples per acquisition (default: 400).
    """
    # Plot data signals in A-mode
    data_signal_count = 0
    for sig_name, sig_data in signals.items():
        if sig_name not in ["timestamp", "trigger"]:
            plot_signal_amode(sig_name, sig_data, samples_per_acquisition)
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
        help="Display ultrasound data in A-mode with acquisition slider",
    )
    parser.add_argument(
        "--samples-per-acquisition",
        type=int,
        default=400,
        help="Number of samples per acquisition for A-mode (default: 400)",
    )

    args = parser.parse_args()

    # Read signals
    signals = read_bio_file(args.file_path)

    # Plot based on mode
    if args.ultrasound:
        plot_ultrasound_amode(signals, args.samples_per_acquisition)
    else:
        plot_standard(signals)


if __name__ == "__main__":
    main()
