# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Shared helpers for locating and reading collected .bio files.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np  # type: ignore[import-not-found]

from biogui import paths


_DTYPE_MAP = {
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


@dataclass(frozen=True)
class LoadedBioFile:
    """Parsed representation of a collected .bio file."""

    path: Path
    signals: dict[str, dict]
    metadata: dict[str, object]


def find_latest_bio_file(runtime_dir: Path | None = None) -> Path | None:
    """Return the newest .bio file in the active runtime directory."""
    search_dir = runtime_dir or paths.DATARUNTIME_DIR
    if not search_dir.exists():
        return None

    bio_files = [candidate for candidate in search_dir.glob("*.bio") if candidate.is_file()]
    if not bio_files:
        return None

    return max(bio_files, key=lambda candidate: (candidate.stat().st_mtime, candidate.name))


def load_bio_file(file_path: Path) -> LoadedBioFile:
    """Read a .bio file produced by the streaming controller."""
    with open(file_path, "rb") as file_handle:
        n_signals = struct.unpack("<I", file_handle.read(4))[0]
        fs_base, n_samp_base = struct.unpack("<fI", file_handle.read(8))

        signals: dict[str, dict] = {}
        for _ in range(n_signals):
            sig_name_len = struct.unpack("<I", file_handle.read(4))[0]
            sig_name = struct.unpack(f"<{sig_name_len}s", file_handle.read(sig_name_len))[
                0
            ].decode()
            fs, n_samp, n_ch, dtype_code = struct.unpack("<f2Ic", file_handle.read(13))

            signals[sig_name] = {
                "fs": fs,
                "n_samp": n_samp,
                "n_ch": n_ch,
                "dtype": _DTYPE_MAP[dtype_code.decode("ascii")],
            }

        has_trigger = struct.unpack("<?", file_handle.read(1))[0]
        has_trigger_str = struct.unpack("<?", file_handle.read(1))[0]

        metadata: dict[str, object] = {
            "fs_base": fs_base,
            "has_trigger": has_trigger,
            "has_trigger_str": has_trigger_str,
        }

        timestamp = np.frombuffer(file_handle.read(8 * n_samp_base), dtype=np.float64).reshape(
            n_samp_base, 1
        )
        signals["timestamp"] = {"data": timestamp, "fs": fs_base}

        for sig_name, sig_data in signals.items():
            if sig_name == "timestamp":
                continue

            n_samp = int(sig_data.pop("n_samp"))
            n_ch = int(sig_data.pop("n_ch"))
            dtype = sig_data.pop("dtype")
            data = np.frombuffer(
                file_handle.read(dtype.itemsize * n_samp * n_ch), dtype=dtype
            ).reshape(n_samp, n_ch)
            sig_data["data"] = data

        if has_trigger:
            trigger = np.frombuffer(file_handle.read(4 * n_samp_base), dtype=np.uint32).reshape(
                n_samp_base, 1
            )
            signals["trigger"] = {"data": trigger, "fs": fs_base}

        if has_trigger_str:
            trigger_str: list[str] = []
            for _ in range(n_samp_base):
                (length,) = struct.unpack("<I", file_handle.read(4))
                if length == 0:
                    trigger_str.append("")
                else:
                    trigger_str.append(file_handle.read(length).decode("utf-8", errors="replace"))

            signals["trigger_str"] = {
                "data": np.array(trigger_str, dtype=object).reshape(n_samp_base, 1),
                "fs": fs_base,
            }
    print(
        f"Loaded .bio file from {file_path} with signals: {list(signals.keys())} and metadata: {metadata}"
    )
    return LoadedBioFile(path=file_path, signals=signals, metadata=metadata)
