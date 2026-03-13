# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Debug triggers from .bio files.


Copyright 2025 Enzo Baraldi (modifications)

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
import os
import struct
import sys

import numpy as np


def read_bio_file(file_path: str) -> dict:
    """
    Read a .bio file and return signals and triggers.
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
        # Read number of signals
        n_signals = struct.unpack("<I", f.read(4))[0]

        # Read base metadata
        fs_base, n_samp_base = struct.unpack("<fI", f.read(8))
        signals = {}

        # Read signal metadata
        for _ in range(n_signals):
            sig_name_len = struct.unpack("<I", f.read(4))[0]
            sig_name = struct.unpack(f"<{sig_name_len}s", f.read(sig_name_len))[0].decode()
            fs, n_samp, n_ch, dtype = struct.unpack("<f2Ic", f.read(13))
            dtype = dtypeMap[dtype.decode("ascii")]

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
        ts = np.frombuffer(f.read(8 * n_samp_base), dtype=np.float64).reshape(n_samp_base, 1)
        signals["timestamp"] = {"data": ts, "fs": fs_base}

        # 2. Signals data
        for sig_name, sig_data in signals.items():
            if sig_name == "timestamp":
                continue

            n_samp = sig_data.pop("n_samp")
            n_ch = sig_data.pop("n_ch")
            dtype = sig_data.pop("dtype")
            data = np.frombuffer(f.read(dtype.itemsize * n_samp * n_ch), dtype=dtype).reshape(
                n_samp, n_ch
            )
            sig_data["data"] = data

        # 3. Trigger (optional)
        trigger = None
        if is_trigger:
            # Read rest of file as trigger data
            trigger = np.frombuffer(f.read(), dtype=np.uint32)

    return {"signals": signals, "trigger": trigger}


def print_file_info(signals: dict, trigger: np.ndarray):
    """
    Print information about the .bio file format and detected signals.
    """
    print("=" * 60)
    print("FILE INFORMATION")
    print("=" * 60)

    # Count signal types
    signal_names = [s for s in signals.keys() if s != "timestamp"]
    print(f"\nDetected {len(signal_names)} signal(s):")
    for sig_name in signal_names:
        sig_data = signals[sig_name]
        print(
            f"  - {sig_name}: {sig_data['data'].shape[0]} samples, "
            f"{sig_data['data'].shape[1]} channel(s), "
            f"fs={sig_data['fs']:.2f} Hz, dtype={sig_data['data'].dtype}"
        )

    # Check for acquisition_number and tx_rx_id signals (format detection)
    has_acquisition_number = "acquisition_number" in signals
    has_tx_rx_id = "tx_rx_id" in signals

    if has_acquisition_number and has_tx_rx_id:
        print("\n   This file includes ACQUISITION_NUMBER and TX_RX_ID data (newest format)")
    elif has_acquisition_number:
        print("\n   This file includes ACQUISITION_NUMBER data (new format, no tx_rx_id)")
    else:
        print("\n⚠ This file does NOT include acquisition_number data (old format)")

    # Trigger info
    if trigger is not None:
        print(f"\nTrigger data present: {len(trigger)} samples")
    else:
        print("\nNo trigger data in this file")

    print("=" * 60)
    print()


def analyze_triggers(trigger_data: np.ndarray):
    """
    Analyzes and prints statistics about the trigger blocks.
    """
    if trigger_data is None:
        print("[-] No trigger data found in this file.")
        return

    # Filter REST (assuming 0 is rest)
    non_rest = trigger_data[trigger_data != 0]

    blocks = []
    if len(non_rest) > 0:
        current_val = non_rest[0]
        current_count = 1

        for val in non_rest[1:]:
            if val == current_val:
                current_count += 1
            else:
                blocks.append((current_val, current_count))
                current_val = val
                current_count = 1
        blocks.append((current_val, current_count))

    if not blocks:
        print("[-] Trigger channel found, but contains no non-zero events.")
        return

    print("Blocks:")
    print("-" * 30)
    for i, (val, count) in enumerate(blocks):
        # Dynamic label mapping based on user logic
        label = "fist" if val == 1 else ("open" if val == 2 else "unknown")
        print(f"{i + 1:2d}. {label:<7} (Val: {val}): {count} samples")

    print("-" * 30)
    fist_blocks = [c for v, c in blocks if v == 1]
    open_blocks = [c for v, c in blocks if v == 2]

    print(f"Fist blocks count: {len(fist_blocks)} | Samples: {fist_blocks}")
    print(f"Open blocks count: {len(open_blocks)} | Samples: {open_blocks}")
    print("-" * 30)

    sum_fist = sum(fist_blocks)
    sum_open = sum(open_blocks)

    print(f"Total samples fist: {sum_fist}")
    print(f"Total samples open: {sum_open}")
    print(f"Difference        : {sum_fist - sum_open}")


def main():
    # Setup CLI arguments
    parser = argparse.ArgumentParser(description="Analyze triggers inside a .bio file.")
    parser.add_argument("filename", type=str, help="Path to the .bio file to analyze")

    args = parser.parse_args()

    # Check if file exists
    if not os.path.isfile(args.filename):
        print(f"Error: File '{args.filename}' not found.")
        sys.exit(1)

    print(f"Processing: {args.filename} ...\n")

    try:
        data = read_bio_file(args.filename)

        # Print file format information
        print_file_info(data["signals"], data["trigger"])

        # Analyze triggers
        analyze_triggers(data["trigger"])
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
