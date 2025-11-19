import struct

import numpy as np


def read_bio_file(file_path: str) -> dict:
    """
    Read a .bio file and return signals and triggers.

    Parameters
    ----------
    file_path : str
        Path to the .bio file.

    Returns
    -------
    dict
        Dictionary with keys:
        - 'signals': Dict of signal_name -> {'data': np.ndarray, 'fs': float}
        - 'trigger': np.ndarray (1D array of trigger values)
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
            trigger = np.frombuffer(f.read(), dtype=np.uint32)

    return {"signals": signals, "trigger": trigger}


file = "/home/enzo/Documents/ba-thesis/biogui/wulpus_fist_open_2025-11-16_12-36-53.bio"
# file = "/home/enzo/Documents/ba-thesis/biogui/wulpus_open_fist_2025-11-18_09-45-45.bio"
data = read_bio_file(file)
trigger = data["trigger"]

# Filter REST
non_rest = trigger[trigger != 0]

# Count blocks
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

print("Blocks:")
for i, (val, count) in enumerate(blocks):
    label = "fist" if val == 1 else "open"
    print(f"{i + 1:2d}. {label} ({val}): {count}")

print()
fist_blocks = [c for v, c in blocks if v == 1]
open_blocks = [c for v, c in blocks if v == 2]
print(f"Fist blocks ({len(fist_blocks)}): {fist_blocks}")
print(f"Open blocks ({len(open_blocks)}): {open_blocks}")
print()
print(f"Total fist: {sum(fist_blocks)}")
print(f"Total open: {sum(open_blocks)}")
print(f"Difference: {sum(fist_blocks) - sum(open_blocks)}")
