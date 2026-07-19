# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Time-series post-run plotting for collected .bio files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .bio_file_utils import LoadedBioFile, find_latest_bio_file, load_bio_file
from .registry import register_plotter

# Signals that are never shown as plottable channels. These are WULPUS/WULPUS Pro
# ultrasound framing signals and never appear in a pure time-series recording, but
# are excluded defensively in case this is invoked on a mixed file.
_NON_CHANNEL_SIGNALS = {
    "acquisition_number",
    "tx_rx_id",
    "wulpus_counter",
    "wulpus_timestamp",
}


def _resolve_enabled_signal_names(
    signal_names: list[str],
    plot_options: dict | None,
) -> list[str]:
    """Filter top-level signal names using plot_options['enabledChannels'] (keyed by signal name)."""
    if not plot_options:
        return signal_names

    enabled_channels = plot_options.get("enabledChannels")

    if isinstance(enabled_channels, dict):
        filtered = [name for name in signal_names if enabled_channels.get(name, True)]
        return filtered or signal_names

    if isinstance(enabled_channels, (list, tuple, set)):
        filtered = [name for name in signal_names if name in enabled_channels]
        return filtered or signal_names

    return signal_names


def _flatten_channels(loaded: LoadedBioFile, signal_names: list[str]) -> dict[str, dict]:
    """Flatten each selected signal's (nSamples, nCh) array into one row per physical channel."""
    channels: dict[str, dict] = {}
    for sig_name in signal_names:
        sig_data = loaded.signals[sig_name]
        data = sig_data["data"]
        fs = sig_data["fs"]
        n_ch = data.shape[1]
        for i in range(n_ch):
            ch_name = f"{sig_name}[{i}]" if n_ch > 1 else sig_name
            channels[ch_name] = {
                "data": data[:, i],
                "fs": fs,
                "sigName": sig_name,
                "chIdx": i,
            }
    return channels


def _find_trigger_track(
    loaded: LoadedBioFile,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    """Find the first signal carrying a trigger track and build a relative-time axis for it.

    Trigger/trigger_str entries are recorded once per incoming packet (not once per
    sample), synchronized with that same signal's own "timestamp" array (packet
    arrival times, in absolute epoch seconds) — every signal decoded from the same
    data source shares the same trigger value per packet, so any signal carrying a
    trigger track is an equally valid source. Returns (trigger_ids, trigger_strs,
    trigger_t_seconds) relative to the first recorded timestamp, or (None, None, None)
    if no signal in the file carries a trigger.
    """
    for sig_data in loaded.signals.values():
        if "trigger" not in sig_data:
            continue
        trigger_ids = np.asarray(sig_data["trigger"]).reshape(-1)
        trigger_strs = np.asarray(sig_data["trigger_str"]).reshape(-1)
        timestamps = np.asarray(sig_data["timestamp"]).reshape(-1)

        n = min(len(trigger_ids), len(trigger_strs), len(timestamps))
        if n == 0:
            continue
        trigger_ids = trigger_ids[:n]
        trigger_strs = trigger_strs[:n]
        trigger_t = timestamps[:n] - timestamps[0]
        return trigger_ids, trigger_strs, trigger_t

    return None, None, None


def plot_latest_time_series_run(
    runtime_dir: Path | None = None,
    plot_options: dict | None = None,
) -> Path | None:
    bio_file = find_latest_bio_file(runtime_dir)

    if bio_file is None:
        print("No .bio file found for post-run plotting.")
        return None

    plot_file(bio_file, plot_options)
    return bio_file


# Module-level list that keeps TimeSeriesPlotWindow instances alive after plot_file returns.
_active_windows: list = []


def plot_file(
    file_path: Path,
    plot_options: dict | None = None,
) -> dict[str, dict]:
    """Load, process and display a .bio file's time-series signals in the Qt post-run window."""
    from .time_series_plot_window import TimeSeriesPlotWindow

    loaded = load_bio_file(file_path)

    signal_names = [name for name in loaded.signals if name not in _NON_CHANNEL_SIGNALS]
    signal_names = _resolve_enabled_signal_names(signal_names, plot_options)

    channels = _flatten_channels(loaded, signal_names)
    if not channels:
        print(f"No time-series data to display for {file_path.name}")
        return channels

    trigger, trigger_str, trigger_t = _find_trigger_track(loaded)

    window = TimeSeriesPlotWindow(
        file_path=file_path,
        channels=channels,
        trigger=trigger,
        trigger_str=trigger_str,
        trigger_t=trigger_t,
        plot_options=plot_options,
    )
    _active_windows.append(window)
    window.destroyed.connect(
        lambda: _active_windows.remove(window) if window in _active_windows else None
    )
    window.show()

    return channels


register_plotter("time-series", plot_latest_time_series_run)
