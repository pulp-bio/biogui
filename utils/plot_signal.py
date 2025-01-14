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
            fs, n_samp, n_ch = struct.unpack("<f2I", f.read(12))

            # Initialize signal array
            signals[sig_name] = {
                "fs": fs,
                "n_samp": n_samp,
                "n_ch": n_ch,
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
            data = np.frombuffer(f.read(4 * n_samp * n_ch), dtype=np.float32).reshape(
                n_samp, n_ch
            )
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

    # Plot
    for sig_name, sig_data in signals.items():
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

    plt.show()


if __name__ == "__main__":
    main()
