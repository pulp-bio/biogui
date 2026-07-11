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
    """
    Read a .bio file produced by the streaming controller.

    Each signal is self-contained: its own data block, immediately followed by its own
    timestamp block (one float64 biogui-arrival timestamp per received packet for that
    signal) and, only if that signal actually recorded a trigger, its own trigger /
    trigger_str blocks. There is no shared/global timestamp or trigger anymore - different
    signals can arrive at different rates (e.g. multi-modal acquisitions), so each carries
    its own.
    """
    with open(file_path, "rb") as file_handle:
        n_signals = struct.unpack("<I", file_handle.read(4))[0]

        headers = []
        for _ in range(n_signals):
            sig_name_len = struct.unpack("<I", file_handle.read(4))[0]
            sig_name = struct.unpack(f"<{sig_name_len}s", file_handle.read(sig_name_len))[
                0
            ].decode()
            fs, n_samp, n_ch, dtype_code, n_samp_ts, n_samp_trigger = struct.unpack(
                "<f2Ic2I", file_handle.read(21)
            )
            headers.append(
                {
                    "name": sig_name,
                    "fs": fs,
                    "n_samp": n_samp,
                    "n_ch": n_ch,
                    "dtype": _DTYPE_MAP[dtype_code.decode("ascii")],
                    "n_samp_ts": n_samp_ts,
                    "n_samp_trigger": n_samp_trigger,
                }
            )

        signals: dict[str, dict] = {}
        has_trigger = False
        for header in headers:
            dtype = header["dtype"]
            data = np.frombuffer(
                file_handle.read(dtype.itemsize * header["n_samp"] * header["n_ch"]),
                dtype=dtype,
            ).reshape(header["n_samp"], header["n_ch"])

            timestamp = np.frombuffer(
                file_handle.read(8 * header["n_samp_ts"]), dtype=np.float64
            ).reshape(header["n_samp_ts"], 1)

            sig_data: dict[str, object] = {"data": data, "fs": header["fs"], "timestamp": timestamp}

            if header["n_samp_trigger"]:
                has_trigger = True
                trigger_ids = np.empty(header["n_samp_trigger"], dtype=np.uint32)
                trigger_strs: list[str] = []
                for i in range(header["n_samp_trigger"]):
                    (trigger_ids[i],) = struct.unpack("<I", file_handle.read(4))
                    (length,) = struct.unpack("<I", file_handle.read(4))
                    trigger_strs.append(
                        file_handle.read(length).decode("utf-8", errors="replace")
                        if length
                        else ""
                    )
                sig_data["trigger"] = trigger_ids.reshape(-1, 1)
                sig_data["trigger_str"] = np.array(trigger_strs, dtype=object).reshape(-1, 1)

            signals[header["name"]] = sig_data

        metadata: dict[str, object] = {
            "n_signals": n_signals,
            "has_trigger": has_trigger,
        }
    print(
        f"Loaded .bio file from {file_path} with signals: {list(signals.keys())} and metadata: {metadata}"
    )
    return LoadedBioFile(path=file_path, signals=signals, metadata=metadata)
