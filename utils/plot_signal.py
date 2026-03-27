# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This script reads the .bio file and plots the acquired signal.
"""

import argparse
import struct
import sys

import numpy as np
from matplotlib import pyplot as plt


def read_bio_file(file_path: str) -> dict:
    """
    Read a .bio file and extract all signals, acq_tss, and triggers.
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

    with open(file_path, "rb") as f:
        n_signals = struct.unpack("<I", f.read(4))[0]
        fs_base, n_samp_base = struct.unpack("<fI", f.read(8))

        signals = {}
        for _ in range(n_signals):
            sig_name_len = struct.unpack("<I", f.read(4))[0]
            sig_name = struct.unpack(f"<{sig_name_len}s", f.read(sig_name_len))[
                0
            ].decode()
            fs, n_samp, n_ch, dtype = struct.unpack("<f2Ic", f.read(13))

            signals[sig_name] = {
                "fs": fs,
                "n_samp": n_samp,
                "n_ch": n_ch,
                "dtype": dtypeMap[dtype.decode("ascii")],
            }

        is_trigger = struct.unpack("<?", f.read(1))[0]
        is_trigger_str = struct.unpack("<?", f.read(1))[0]

        # 1. Acquisition timestamp
        ts = np.frombuffer(f.read(8 * n_samp_base), dtype=np.float64).reshape(
            n_samp_base, 1
        )
        signals["acq_ts"] = {"data": ts, "fs": fs_base}

        # 2. Signals data
        for sig_name, sig_data in signals.items():
            if sig_name == "acq_ts":
                continue

            n_samp = sig_data.pop("n_samp")
            n_ch = sig_data.pop("n_ch")
            dtype = sig_data.pop("dtype")

            data = np.frombuffer(
                f.read(dtype.itemsize * n_samp * n_ch), dtype=dtype
            ).reshape(n_samp, n_ch)
            sig_data["data"] = data

        # 3. Trigger
        if is_trigger:
            itemsize = 4  # saving as uint32_t
            trigger = np.frombuffer(
                f.read(itemsize * n_samp_base), dtype=np.uint32
            ).reshape(n_samp_base, 1)
            signals["trigger"] = {"data": trigger, "fs": fs_base}
            # 4. Trigger string (len-prefixed UTF-8 per sample)
            if is_trigger_str:
                trigger_str = []
                for _ in range(n_samp_base):
                    (L,) = struct.unpack("<I", f.read(4))
                    if L == 0:
                        trigger_str.append("")
                    else:
                        b = f.read(L)
                        trigger_str.append(b.decode("utf-8", errors="replace"))

            # store as (n_samp_base, 1) like other signals
            signals["trigger_str"] = {
                "data": np.array(trigger_str, dtype=object).reshape(n_samp_base, 1),
                "fs": fs_base,
            }

    return signals


def plot_signal_mmode(
    sig_name: str, sig_data: dict, samples_per_acquisition: int = 397
):
    """
    Plot a single signal in M-mode (time vs depth).
    Removed colorbar/intensity scale.
    """
    data = sig_data["data"]
    fs = sig_data["fs"]
    n_samp, n_ch = data.shape

    n_acquisitions = n_samp // samples_per_acquisition

    if n_acquisitions == 0:
        print(f"Warning: Signal '{sig_name}' skipped (not enough samples).")
        return

    # Reshape data
    truncated_samples = n_acquisitions * samples_per_acquisition
    data_reshaped = data[:truncated_samples, :].reshape(
        n_acquisitions, samples_per_acquisition, n_ch
    )

    # Axes setup
    acquisition_duration = samples_per_acquisition / fs
    time_axis = np.arange(n_acquisitions) * acquisition_duration
    depth_axis = np.arange(samples_per_acquisition)

    fig, axes = plt.subplots(
        nrows=n_ch, sharex=True, figsize=(16, n_ch * 4), layout="constrained"
    )
    if n_ch == 1:
        axes = [axes]

    fig.suptitle(f"{sig_name} - M-mode")

    for i in range(n_ch):
        mmode_data = data_reshaped[:, :, i].T

        # Dynamic level range calculation
        data_min, data_max = mmode_data.min(), mmode_data.max()
        level_range = (data_max - data_min) if data_max != data_min else 1.0
        vmin, vmax = data_min - 0.1 * level_range, data_max + 0.1 * level_range

        # Plot without assigning to variable 'im', since we don't need the handle for colorbar
        axes[i].imshow(
            mmode_data,
            aspect="auto",
            cmap="gray",
            extent=[time_axis[0], time_axis[-1], depth_axis[-1], depth_axis[0]],
            interpolation="nearest",
            vmin=vmin,
            vmax=vmax,
        )
        axes[i].set_ylabel(f"Channel {i}\nDepth (sample)")
        axes[i].grid(False)

    axes[-1].set_xlabel("Time (s)")


def plot_signal_standard(sig_name: str, sig_data: dict):
    """Standard plot for a single signal."""
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


def plot_ultrasound_mmode(signals: dict, samples_per_acquisition: int = 397):
    """Orchestrator for M-mode plotting."""
    data_signal_count = 0
    for sig_name, sig_data in signals.items():
        if sig_name not in [
            "acq_ts",
            "trigger",
            "imu",
            "acquisition_number",
            "tx_rx_id",
        ]:
            plot_signal_mmode(sig_name, sig_data, samples_per_acquisition)
            data_signal_count += 1

    if data_signal_count == 0:
        sys.exit("Error: No data signals found.")

    for sig_name, sig_data in signals.items():
        if sig_name in [
            "acq_ts",
            "trigger",
            "imu",
            "acquisition_number",
            "tx_rx_id",
        ]:
            plot_signal_standard(sig_name, sig_data)

    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot signals from .bio files")
    parser.add_argument("file_path", type=str, help="Path to the .bio file")
    parser.add_argument(
        "--ultrasound", action="store_true", help="Display ultrasound data in M-mode"
    )
    parser.add_argument(
        "--samples-per-acquisition",
        type=int,
        default=397,
        help="Samples per acquisition (default: 397)",
    )

    args = parser.parse_args()
    signals = read_bio_file(args.file_path)

    if args.ultrasound:
        plot_ultrasound_mmode(signals, args.samples_per_acquisition)
    else:
        # Plot all signals except acquisition_number and tx_rx_id (not interesting for visualization)
        for sig_name, sig_data in signals.items():
            if sig_name not in ["acquisition_number", "tx_rx_id"]:
                plot_signal_standard(sig_name, sig_data)
        plt.show()


if __name__ == "__main__":
    main()
