"""
Registry for post-run plotters.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable


PlotterFn = Callable[[Path | None, dict | None], Path | None]

_PLOTTERS: dict[str, PlotterFn] = {}


def register_plotter(plotter_key: str, plotter_fn: PlotterFn) -> None:
    """Register a plotter callable under a stable key."""
    _PLOTTERS[plotter_key] = plotter_fn


def get_plotter(plotter_key: str) -> PlotterFn | None:
    """Return a registered plotter, loading built-in plotters lazily if needed."""
    plotter = _PLOTTERS.get(plotter_key)
    if plotter is not None:
        return plotter

    if plotter_key == "ultrasound":
        from . import ultrasound  # noqa: F401
        logging.info("Loaded built-in ultrasound plotter.")
        return _PLOTTERS.get(plotter_key)

    return None


def plot_latest_runtime_file(
    plotter_key: str,
    runtime_dir: Path | None = None,
    plot_options: dict | None = None,
) -> Path | None:
    """Run the requested plotter against the newest runtime file."""
    plotter = get_plotter(plotter_key)
    if plotter is None:
        logging.warning("Requested plotter not found.")
        return None
    return plotter(runtime_dir, plot_options)