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
            sig_name = struct.unpack(f"<{sig_name_len}s", f.read(sig_name_len))[
                0
            ].decode()
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
        trigger = None
        if is_trigger:
            # Read rest of file as trigger data
            trigger = np.frombuffer(f.read(), dtype=np.uint32)

    return {"signals": signals, "trigger": trigger}


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
        analyze_triggers(data["trigger"])
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
