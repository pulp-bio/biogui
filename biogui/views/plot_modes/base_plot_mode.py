from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque

import numpy as np


class BasePlotMode(ABC):
    """
    Abstract base class for different plot modes.

    Parameters
    ----------
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels.
    chSpacing : float
        Spacing between each channel in the plot.
    **config : dict
        Additional configuration options.

    Attributes
    ----------
    fs : float
        Sampling frequency.
    n_ch : int
        Number of channels.
    ch_spacing : float
        Spacing between channels.
    config : dict
        Configuration dictionary.
    _sample_count : int
        Counter for tracking samples (used for SPS calculation).
    """

    def __init__(
        self,
        fs: float,
        nCh: int,
        chSpacing: float,
        **config: dict,
    ) -> None:
        self.fs = fs
        self.n_ch = nCh
        self.ch_spacing = chSpacing
        self.config = config
        self._sample_count = 0

    @property
    def sample_count(self) -> int:
        """Get the current sample count and reset it."""
        count = self._sample_count
        self._sample_count = 0
        return count

    @abstractmethod
    def add_data(self, data: np.ndarray) -> None:
        """
        Add incoming data to internal buffer.

        Parameters
        ----------
        data : ndarray
            Data to add (shape: [n_samples, n_channels]).
        """
        pass

    @abstractmethod
    def has_new_data(self) -> bool:
        """Check if there's new data ready to be rendered."""
        pass

    @abstractmethod
    def render(self) -> None:
        """Render the current state to the plot."""
        pass

    @abstractmethod
    def setup_plot(self, graph_widget) -> None:
        """
        Initial plot setup (axes, items, etc.).

        Parameters
        ----------
        graph_widget : PlotWidget
            The pyqtgraph PlotWidget to setup.
        """
        pass

    @abstractmethod
    def get_elapsed_time(self) -> float:
        """Get the elapsed time in seconds."""
        pass

    def get_data_queue(self) -> deque:
        """
        Get a representation of the current data as a queue.

        This is used for mode switching to transfer data between modes.

        Returns
        -------
        deque
            A deque containing the current data.
        """
        # Default implementation returns empty queue
        # Subclasses should override if they support data transfer
        from collections import deque

        return deque()
