from __future__ import annotations

from collections import deque

import numpy as np
import pyqtgraph as pg

from .base_plot_mode import BasePlotMode


class TimeSeriesPlotMode(BasePlotMode):
    """
    Plot mode for continuous time-series data.

    Parameters
    ----------
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels.
    chSpacing : float
        Spacing between each channel in the plot.
    renderLenMs : int
        Length of the window in the plot (in ms).
    **config : dict
        Additional configuration options, including:
        - dataQueue: Optional pre-existing data queue
        - minRange: Optional minimum Y range
        - maxRange: Optional maximum Y range

    Attributes
    ----------
    _data_queue : deque
        Ring buffer for storing data to display.
    _plots : list
        List of PlotDataItem references.
    _time_tracker : int
        Tracker for elapsed samples.
    """

    def __init__(
        self,
        fs: float,
        nCh: int,
        chSpacing: float,
        renderLenMs: int,
        **config: dict,
    ) -> None:
        super().__init__(fs, nCh, chSpacing, **config)

        # Calculate render length in samples
        render_len_samples = int(round(renderLenMs / 1000 * fs))

        # Initialize data queue
        self._data_queue = deque(maxlen=render_len_samples)

        # Pre-fill with existing data or zeros
        if "dataQueue" in config:
            self._data_queue.extend(config["dataQueue"])
        else:
            for _ in range(render_len_samples):
                self._data_queue.append(np.zeros(nCh))

        self._plots = []
        self._time_tracker = 0
        self._graph_widget = None

    def add_data(self, data: np.ndarray) -> None:
        """Add data to the queue."""
        self._data_queue.extend(data)
        self._sample_count += data.shape[0]
        self._time_tracker += data.shape[0]

    def has_new_data(self) -> bool:
        """Time-series always renders on refresh."""
        return len(self._data_queue) > 0

    def setup_plot(self, graph_widget) -> None:
        """Setup line plots for each channel."""
        self._graph_widget = graph_widget
        graph_widget.clear()

        # Hide bottom axis for time-series
        graph_widget.getPlotItem().hideAxis("bottom")

        # Set Y range if provided
        if "minRange" in self.config and "maxRange" in self.config:
            graph_widget.setYRange(self.config["minRange"], self.config["maxRange"])

        # Get colormap
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")  # type: ignore
        lut = cm.getLookupTable(nPts=self.n_ch, mode="qcolor")  # type: ignore

        # Create line plots
        ys = np.asarray(self._data_queue).T
        for i in range(self.n_ch):
            pen = pg.mkPen(color=lut[i], width=1)  # type: ignore
            plot_item = graph_widget.plot(
                ys[i] + self.ch_spacing * (self.n_ch - i - 1),
                pen=pen,
            )
            plot_item.setClipToView(True)
            self._plots.append(plot_item)

    def render(self) -> None:
        """Update the line plots."""
        if not self._plots:
            return

        ys = np.asarray(self._data_queue).T
        for i in range(self.n_ch):
            self._plots[i].setData(
                ys[i] + self.ch_spacing * (self.n_ch - i - 1),
                skipFiniteCheck=True,
            )

    def get_elapsed_time(self) -> float:
        """Calculate elapsed time based on sample count."""
        return self._time_tracker / self.fs

    def reinitialize(self, render_len_ms: int) -> None:
        """Re-initialize with new render length."""
        render_len_samples = int(round(render_len_ms / 1000 * self.fs))
        new_queue = deque(maxlen=render_len_samples)

        # Pre-fill with zeros
        for _ in range(render_len_samples):
            new_queue.append(np.zeros(self.n_ch))

        # Copy existing data
        new_queue.extend(self._data_queue)
        self._data_queue = new_queue

        # Re-setup plot
        if self._graph_widget:
            self._plots = []
            self.setup_plot(self._graph_widget)

    def get_data_queue(self) -> deque:
        """
        Get the data queue for mode switching.

        Returns
        -------
        deque
            The internal data queue.
        """
        return self._data_queue
