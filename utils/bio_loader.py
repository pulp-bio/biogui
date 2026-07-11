"""
BioGUI .bio file reader.

Shared by all platform-specific dataset modules.
"""

import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_DTYPE_MAP: dict[str, np.dtype] = {
    "?": np.dtype("bool"),    "b": np.dtype("int8"),    "B": np.dtype("uint8"),
    "h": np.dtype("int16"),   "H": np.dtype("uint16"),  "i": np.dtype("int32"),
    "I": np.dtype("uint32"),  "q": np.dtype("int64"),   "Q": np.dtype("uint64"),
    "f": np.dtype("float32"), "d": np.dtype("float64"),
}


@dataclass
class BioFile:
    """Parsed .bio file.  Each entry in `signals` has keys: data, fs."""
    path: Path
    signals: dict[str, dict] = field(default_factory=dict)
    metadata: dict           = field(default_factory=dict)


def load_bio_file(file_path: str | Path) -> BioFile:
    """
    Read a .bio file produced by BioGUI's streaming controller.

    Returns a BioFile whose `signals` dict maps signal name -> dict with:
      data      : np.ndarray  shape (n_samp, n_ch)
      fs        : float       sampling rate [Hz]
      timestamp : np.ndarray  shape (n_samp_ts, 1) float64
                  biogui timestamps retrieved when a new data packet is received. 

    Optional keys, present only for signals that actually recorded a trigger:
      trigger     : (n_samp_trigger, 1) uint32  gesture labels
      trigger_str : (n_samp_trigger, 1) object  gesture strings

    Timestamps and triggers are recorded per signal since different signals can arrive at different
    rates (e.g. multi-modal acquisitions).
    """
    file_path = Path(file_path)
    with open(file_path, "rb") as fh:
        n_signals = struct.unpack("<I", fh.read(4))[0]

        headers = []
        for _ in range(n_signals):
            name_len = struct.unpack("<I", fh.read(4))[0]
            name = struct.unpack(f"<{name_len}s", fh.read(name_len))[0].decode()
            fs, n_samp, n_ch, dtype_code, n_samp_ts, n_samp_trigger = struct.unpack(
                "<f2Ic2I", fh.read(21)
            )
            headers.append(
                {
                    "name": name,
                    "fs": float(fs),
                    "n_samp": int(n_samp),
                    "n_ch": int(n_ch),
                    "dtype": _DTYPE_MAP[dtype_code.decode("ascii")],
                    "n_samp_ts": int(n_samp_ts),
                    "n_samp_trigger": int(n_samp_trigger),
                }
            )

        signals: dict[str, dict] = {}
        has_trigger = False
        for h in headers:
            dt = h["dtype"]
            data = np.frombuffer(
                fh.read(dt.itemsize * h["n_samp"] * h["n_ch"]), dtype=dt
            ).reshape(h["n_samp"], h["n_ch"])

            ts = np.frombuffer(fh.read(8 * h["n_samp_ts"]), dtype=np.float64).reshape(
                h["n_samp_ts"], 1
            )

            sig: dict[str, object] = {"data": data, "fs": h["fs"], "timestamp": ts}

            if h["n_samp_trigger"]:
                has_trigger = True
                trig_ids = np.empty(h["n_samp_trigger"], dtype=np.uint32)
                trig_strs: list[str] = []
                for i in range(h["n_samp_trigger"]):
                    (trig_ids[i],) = struct.unpack("<I", fh.read(4))
                    (length,) = struct.unpack("<I", fh.read(4))
                    trig_strs.append(
                        fh.read(length).decode("utf-8", errors="replace") if length else ""
                    )
                sig["trigger"] = trig_ids.reshape(-1, 1)
                sig["trigger_str"] = np.array(trig_strs, dtype=object).reshape(-1, 1)

            signals[h["name"]] = sig

    metadata = {
        "n_signals": n_signals,
        "has_trigger": has_trigger,
    }
    print(
        f"Loaded {file_path.name}  signals={list(signals.keys())}  has_trigger={has_trigger}"
    )
    return BioFile(path=file_path, signals=signals, metadata=metadata)

