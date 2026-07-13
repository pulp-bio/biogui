"""
Ultrasound (WULPUS / WULPUS PRO) reconstruction and post-run plotting from a .bio file.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from bio_loader import load_bio_file
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
from scipy.signal import hilbert


# ── Trigger coloring helpers (duplicated in emg_utils.py / manus_utils.py) ──────────────────

_NEUTRAL_LABELS = {"", "rest", "init", "finished", "nan"}
_TRIGGER_CMAP = plt.get_cmap("tab10")


def _clean_labels(trigger_str) -> np.ndarray:
    """String labels with NaN (dropped-frame gaps) filled from neighboring samples - a brief
    1-few-sample dropout shouldn't fragment an otherwise-continuous gesture segment into several
    pieces separated by a spurious gap."""
    filled = pd.Series(trigger_str).ffill().bfill()
    return np.array(["" if pd.isna(v) else str(v) for v in filled])


def _gesture_labels(trigger_str) -> list[str]:
    """Unique real-gesture labels (excludes rest/init/finished/empty), in first-seen order."""
    seen: list[str] = []
    for label in _clean_labels(trigger_str):
        if label not in _NEUTRAL_LABELS and label not in seen:
            seen.append(label)
    return seen


def _color_for(label: str, gestures: list[str]):
    if label in _NEUTRAL_LABELS:
        return (0.85, 0.85, 0.85)
    return _TRIGGER_CMAP(gestures.index(label) % 10)


def _trigger_segments(trigger_str):
    """Yield (start, end, label) for each contiguous run of the same trigger label."""
    labels = _clean_labels(trigger_str)
    if len(labels) == 0:
        return
    change = np.where(labels[1:] != labels[:-1])[0] + 1
    bounds = np.concatenate(([0], change, [len(labels)]))
    for start, end in zip(bounds[:-1], bounds[1:]):
        yield start, end, labels[start]


def _trigger_track(ax, t, trigger_str, legend: bool = True) -> None:
    """Draw an opaque, color-coded gesture timeline strip on ax, with an optional legend."""
    gestures = _gesture_labels(trigger_str)
    for start, end, label in _trigger_segments(trigger_str):
        ax.axvspan(t[start], t[min(end, len(t) - 1)], color=_color_for(label, gestures), lw=0)
    if gestures and legend:
        handles = [plt.Rectangle((0, 0), 1, 1, color=_color_for(g, gestures)) for g in gestures]
        ax.legend(handles, gestures, loc="upper right", fontsize=6, ncol=min(len(gestures), 6), framealpha=0.9)
    ax.set_yticks([])
    ax.set_ylim(0, 1)


# ── Processing ───────────────────────────────────────────────────────────────────────────────


def _cfg_num(name: str) -> int:
    """Config number encoded in an ultrasound signal name, or 0 for a bare 'ultrasound'
    signal (the single-RX-channel default: no "_cfgN_rxM" suffix is added in that case,
    see biogui.platforms.wulpus(_pro).runtime)."""
    match = re.search(r"cfg(\d+)", name)
    return int(match.group(1)) if match else 0


def process_ultrasound(
    signals: dict,
    us_samples_per_frame: int = 400,
) -> pd.DataFrame:
    """
    Reconstruct a per-frame ultrasound dataframe: one row per completed frame, across all
    configured RX channels, sorted by acquisition order. Works for both source platforms:

    - WULPUS PRO: frames are counted/timestamped by the nRF firmware itself ("wulpus_counter" /
      "wulpus_timestamp" signals, one BLE chunk-reassembled frame at a time).
    - Plain WULPUS: the firmware does not add its own per-frame counter/timestamp, so
      "acquisition_number" (also emitted every frame) plus that signal's own biogui
      (host-arrival) timestamp is used instead; "nrf_wulpus_timestamp" is left NaN in this
      case since no such hardware field exists.
    """
    is_pro = "wulpus_counter" in signals
    counter_sig = "wulpus_counter" if is_pro else "acquisition_number"

    frame_counter = np.unwrap(signals[counter_sig]["data"].ravel().astype(np.int64), period=65536)
    frame_counter_ts = signals[counter_sig]["timestamp"].ravel()
    if is_pro:
        hw_timestamp = signals["wulpus_timestamp"]["data"].ravel().astype(np.int64)
    else:
        hw_timestamp = np.full(frame_counter.shape, np.nan)
    tx_rx_ids = signals["tx_rx_id"]["data"].ravel()

    has_trigger = "trigger" in signals[counter_sig]
    if has_trigger:
        frame_trigger = signals[counter_sig]["trigger"].ravel()
        frame_trigger_str = signals[counter_sig]["trigger_str"].ravel()

    has_imu = "imu" in signals
    if has_imu:
        imu_data = signals["imu"]["data"]

    us_channel_names = sorted(
        (name for name in signals if name == "ultrasound" or name.startswith("ultrasound_")),
        key=_cfg_num,
    )
    num_us_channels = len(us_channel_names)
    if num_us_channels == 0:
        raise ValueError("No 'ultrasound' / 'ultrasound_cfg*' signals found in the .bio file.")

    rows: list[dict] = []
    for cfg_id, sig_name in enumerate(us_channel_names):
        idx = np.where(tx_rx_ids == cfg_id)[0]
        if idx.size == 0:
            continue

        acq_numbers = frame_counter[idx]
        hw_ts = hw_timestamp[idx]
        biogui_ts = frame_counter_ts[idx]
        trig = frame_trigger[idx] if has_trigger else None
        trig_str = frame_trigger_str[idx] if has_trigger else None
        imu = imu_data[idx] if has_imu else None

        us_data = signals[sig_name]["data"]
        n_frames = min(us_data.shape[0] // us_samples_per_frame, len(idx))
        us_data = us_data[: n_frames * us_samples_per_frame].reshape(n_frames, us_samples_per_frame)
        acq_numbers, hw_ts, biogui_ts = acq_numbers[:n_frames], hw_ts[:n_frames], biogui_ts[:n_frames]
        if has_trigger:
            trig, trig_str = trig[:n_frames], trig_str[:n_frames]
        if has_imu:
            imu = imu[:n_frames]

        # Genesis garbage: cfg 0's first frame(s) sometimes arrive all-zero before the ADC settles.
        garbage = np.where(~us_data.any(axis=1))[0]
        if garbage.size:
            if cfg_id != 0:
                print(f"[US] Warning: {sig_name} has {garbage.size} unexpected all-zero frame(s).")
            keep = np.setdiff1d(np.arange(n_frames), garbage)
            us_data, acq_numbers, hw_ts, biogui_ts = us_data[keep], acq_numbers[keep], hw_ts[keep], biogui_ts[keep]
            if has_trigger:
                trig, trig_str = trig[keep], trig_str[keep]
            if has_imu:
                imu = imu[keep]

        if acq_numbers.size > 1 and not np.all(np.diff(acq_numbers) == num_us_channels):
            n_gaps = int(np.sum(np.diff(acq_numbers) != num_us_channels))
            print(f"[US] Warning: {n_gaps} frame gap(s) detected for {sig_name} (dropped packets).")

        for row in range(len(acq_numbers)):
            entry = {
                "cfg_id": cfg_id,
                "wulpus_counter": acq_numbers[row],
                "nrf_wulpus_timestamp": hw_ts[row],
                "biogui_timestamp": biogui_ts[row],
                "ultrasound_data": us_data[row],
            }
            if has_trigger:
                entry["biogui_trigger"] = trig[row]
                entry["biogui_trigger_str"] = trig_str[row]
            if has_imu:
                entry["imu_x"], entry["imu_y"], entry["imu_z"] = imu[row]
            rows.append(entry)

    us_df = pd.DataFrame(rows).sort_values("wulpus_counter").reset_index(drop=True)
    us_df["cfg_id"] = us_df["cfg_id"].astype(float)
    us_df["wulpus_counter"] = us_df["wulpus_counter"].astype(float)
    us_df["nrf_wulpus_timestamp"] = us_df["nrf_wulpus_timestamp"].astype(float)
    if has_trigger:
        us_df["biogui_trigger"] = us_df["biogui_trigger"].astype(float)
    if has_imu:
        for col in ("imu_x", "imu_y", "imu_z"):
            us_df[col] = us_df[col].astype(float)

    us_df["time_ms"] = (us_df["biogui_timestamp"] - us_df["biogui_timestamp"].min()) * 1000.0

    return us_df



ADC_FS = 8e6
SPEED_SOUND_TISSUE = 1540
ADC_START_DELAY = 9e-6
TRANSDUCER_FC = 2.25e6


def compute_us_imaging_depths(adc_start_delay: float = ADC_START_DELAY, n_samples: int = 400) -> np.ndarray:
    """Depth axis [mm] for a WULPUS A-line, exactly as in pipeline_datasynch.ipynb."""
    space_during_delay = adc_start_delay * SPEED_SOUND_TISSUE
    min_depth_mm = round((space_during_delay / 2) * 1000, 2)
    delta_mm = round((SPEED_SOUND_TISSUE / ADC_FS) * 1000, 2) / 2
    return (np.arange(0, n_samples) * delta_mm) + min_depth_mm


def pre_process_ultrasound_data(
    us_array_raw,
    filter: bool = True,
    f_low: float = TRANSDUCER_FC - (TRANSDUCER_FC * 0.20),
    f_high: float = TRANSDUCER_FC + (TRANSDUCER_FC * 0.20),
    hilbert_envelope: bool = True,
):
    """
    Pre-process ultrasound data by applying a bandpass filter and extracting the Hilbert
    envelope, exactly as in pipeline_datasynch.ipynb.
    """
    b, a = signal.butter(2, [f_low / (ADC_FS / 2), f_high / (ADC_FS / 2)], btype="bandpass")
    us_array_filtered = signal.filtfilt(b, a, us_array_raw)
    if hilbert_envelope:
        us_array_env = np.abs(hilbert(us_array_filtered))
        return us_array_filtered, us_array_env
    return us_array_filtered


# ── Plotting ─────────────────────────────────────────────────────────────────────────────────


def plot_ultrasound(us_df: pd.DataFrame, save_path: str | Path | None = None, title: str = "Ultrasound") -> plt.Figure:
    """
    M-mode (bandpass-filtered Hilbert-envelope waterfall) per configured channel, plus an
    optional trigger strip row and an optional IMU row, all sharing one time axis - mirrors
    the Visualization tab of biogui.views.post_run_plotters.post_run_dialog. `us_df` must
    come from `process_ultrasound`, which already adds the "time_ms" column this needs.
    """
    has_trigger = "biogui_trigger_str" in us_df.columns
    has_imu = "imu_x" in us_df.columns
    cfg_ids = sorted(us_df["cfg_id"].dropna().unique())
    n = len(cfg_ids)
    if n == 0:
        raise ValueError("No ultrasound channels found in us_df.")

    img_depths = compute_us_imaging_depths()
    n_rows = 2 * n + (1 if has_trigger else 0) + (1 if has_imu else 0)
    height_ratios = [0.18, 1] * n + ([0.5] if has_trigger else []) + ([0.6] if has_imu else [])
    fig, axs = plt.subplots(
        n_rows, 1, figsize=(14, 1.7 * n + 2 + (1.2 if has_imu else 0)), sharex=True,
        gridspec_kw={"height_ratios": height_ratios},
    )
    axs = np.atleast_1d(axs)

    for i, cfg_id in enumerate(cfg_ids):
        strip_ax, img_ax = axs[2 * i], axs[2 * i + 1]
        sub = us_df[us_df["cfg_id"] == cfg_id].sort_values("time_ms")
        t = sub["time_ms"].to_numpy()

        if has_trigger:
            _trigger_track(strip_ax, t, sub["biogui_trigger_str"].to_numpy(), legend=(i == 0))
        else:
            strip_ax.axis("off")
        strip_ax.set_title(f"cfg {int(cfg_id)}", fontsize=9, loc="left")

        us_array = np.vstack(sub["ultrasound_data"].to_numpy())
        _, us_env = pre_process_ultrasound_data(us_array)
        img_ax.imshow(
            us_env.T,
            aspect="auto",
            cmap="gray",
            extent=[t[0], t[-1], img_depths[-1], img_depths[0]],
        )
        img_ax.set_ylabel("Depth\n[mm]", fontsize=8)

    row = 2 * n
    if has_trigger:
        t_all = us_df["time_ms"].to_numpy()
        axs[row].plot(t_all, us_df["biogui_trigger"].to_numpy(), linewidth=0.8, color="tab:red")
        axs[row].set_ylabel("Trigger\n[raw]", fontsize=8)
        axs[row].grid(True, alpha=0.3)
        row += 1

    if has_imu:
        t_all = us_df["time_ms"].to_numpy()
        for col, color in zip(("imu_x", "imu_y", "imu_z"), ("tab:red", "tab:green", "tab:blue")):
            axs[row].plot(t_all, us_df[col].to_numpy(), linewidth=0.8, color=color, label=col)
        axs[row].set_ylabel("IMU", fontsize=8)
        axs[row].legend(loc="upper right", fontsize=6, ncol=3, framealpha=0.9)
        axs[row].grid(True, alpha=0.3)

    axs[-1].set_xlabel("Time [ms]")
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=150)
        print(f"[US] plot saved to {save_path}")
    return fig


# ── Saving ───────────────────────────────────────────────────────────────────────────────────


def save_ultrasound_dataframe(us_df: pd.DataFrame, save_path: str | Path) -> Path:
    """
    Save the ultrasound dataframe to disk. Dispatches on the file extension:

    - .pkl / .pickle (recommended): preserves the "ultrasound_data" column's per-row numpy
      arrays exactly.
    - .parquet: also preserves array-valued cells, needs `pyarrow` installed.
    - .csv: human-readable, but the "ultrasound_data" waveform is flattened into a
      space-separated string per row (lossy for downstream numeric reloading - reparse with
      `np.fromstring(cell, sep=" ")`).

    Any other/missing extension falls back to pickle, since that is always safe for a
    dataframe with array-valued cells.
    """
    save_path = Path(save_path)
    suffix = save_path.suffix.lower()

    if suffix == ".csv":
        df_out = us_df.copy()
        df_out["ultrasound_data"] = df_out["ultrasound_data"].apply(
            lambda arr: " ".join(str(v) for v in np.asarray(arr).ravel())
        )
        df_out.to_csv(save_path, index=False)
    elif suffix == ".parquet":
        us_df.to_parquet(save_path)
    else:
        if suffix not in (".pkl", ".pickle"):
            save_path = save_path.with_suffix(".pkl")
        us_df.to_pickle(save_path)

    print(f"[US] dataframe saved to {save_path}")
    return save_path


# ── Entry point ──────────────────────────────────────────────────────────────────────────────


def load_and_plot_ultrasound(
    bio_path: str | Path,
    us_samples_per_frame: int = 400,
    save_plot_path: str | Path | None = None,
    save_df_path: str | Path | None = None,
    title: str | None = None,
) -> pd.DataFrame:
    """
    Load a .bio file (WULPUS or WULPUS PRO, auto-detected) and produce the same M-mode /
    IMU / trigger view as biogui's post-run window.

    Parameters
    ----------
    bio_path : str or Path
        Path to the .bio file to load.
    us_samples_per_frame : int, default=400
        Number of ADC samples per ultrasound A-line.
    save_plot_path : str or Path or None
        If given, the M-mode/IMU/trigger figure is also saved there; otherwise it is shown
        interactively.
    save_df_path : str or Path or None
        If given, the reconstructed per-frame dataframe is also saved there (see
        `save_ultrasound_dataframe` for the supported extensions).
    title : str or None
        Plot title; defaults to the .bio file's name.

    Returns
    -------
    pd.DataFrame
        The reconstructed per-frame ultrasound dataframe (one row per frame per channel).
    """
    bio_path = Path(bio_path)
    bio_file = load_bio_file(bio_path)

    us_df = process_ultrasound(bio_file.signals, us_samples_per_frame=us_samples_per_frame)

    plot_ultrasound(us_df, save_path=save_plot_path, title=title or bio_path.name)
    if save_plot_path is None:
        plt.show()

    if save_df_path is not None:
        save_ultrasound_dataframe(us_df, save_df_path)

    return us_df


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconstruct and plot ultrasound (WULPUS / WULPUS PRO) data from a .bio file."
    )
    parser.add_argument("bio_path", type=Path, help="Path to the .bio file to load.")
    parser.add_argument(
        "--us-samples-per-frame",
        type=int,
        default=400,
        help="Number of ADC samples per ultrasound A-line (default: 400).",
    )
    parser.add_argument(
        "--save-plot-path",
        type=Path,
        default=None,
        help="Save the M-mode/IMU/trigger figure here instead of showing it interactively.",
    )
    parser.add_argument(
        "--save-df-path",
        type=Path,
        default=None,
        help="Save the reconstructed dataframe here (.pkl/.parquet/.csv).",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Plot title (default: the .bio file's name).",
    )
    return parser


if __name__ == "__main__":
    cli_args = _build_arg_parser().parse_args()
    load_and_plot_ultrasound(
        bio_path=cli_args.bio_path,
        us_samples_per_frame=cli_args.us_samples_per_frame,
        save_plot_path=cli_args.save_plot_path,
        save_df_path=cli_args.save_df_path,
        title=cli_args.title,
    )



# Example usage from the command line:
#python wulpus_ultrasound_utils.py "...\biogui\biogui\dataruntime\run_2026-07-13_09-05-44.bio" --us-samples-per-frame 397