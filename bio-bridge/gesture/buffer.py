"""
Ultrasound data buffering for gesture recognition.

Provides a unified USDataBuffer class that accumulates ultrasound
data from multiple channels for gesture prediction.
"""

import threading
from collections import deque

import numpy as np

from core import NUM_US_CHANNELS, US_WINDOW_SIZE, NUM_IMU_CHANNELS


class IMUDataBuffer:
    """
    Circular buffer for IMU data.

    Stores the last N IMU samples for each IMU channel.
    """

    def __init__(
        self,
        num_imu_channels: int,
        imu_samples_to_buffer: int,
        thread_safe: bool = False,
        ):
        self.num_imu_channels = num_imu_channels
        self.imu_samples_to_buffer = imu_samples_to_buffer

        # one buffer per IMU channel (e.g., 6 channels: ax,ay,az,gx,gy,gz)
        self.imu_buffer = [
            deque(maxlen=imu_samples_to_buffer)
            for _ in range(self.num_imu_channels)
        ]

        self._lock = threading.Lock() if thread_safe else None


    def _acquire_lock(self):
        if self._lock is not None:
            return self._lock      # real threading.Lock()
        return _DummyLock()        # fake lock that does nothing

    def push_imu_sample(self, imu_sample):
        # imu_sample shape: (3,)
        for ch in range(self.num_imu_channels):
            self.imu_buffer[ch].append(float(imu_sample[ch]))
    
    def get_imu_samples(self):
        with self._acquire_lock():
            return np.array([list(buf) for buf in self.imu_buffer], dtype=np.float32)               # shape: num_imu_channels, imu_samples_to_buffer


class USDataBuffer:
    """
    Buffer for ultrasound data from multiple channels.

    Accumulates ultrasound samples from BioGUI into a format suitable
    for neural network inference. BioGUI sends packets sequentially
    (cfg0, cfg1, cfg2, cfg3, cfg0, cfg1, ...) and this buffer organizes
    them by channel using the tx_rx_id from each packet.

    Parameters
    ----------
    window_size : int, optional
        Number of samples per channel.
    num_channels : int, optional
        Number of ultrasound channels.
    thread_safe : bool, optional
        If True, all operations are protected by a lock for multi-threaded
        access. Defaults to False.

    Attributes
    ----------
    buffers : list[deque]
        Circular buffers for each channel.
    window_size : int
        Number of samples per channel.
    num_channels : int
        Number of channels.
    """

    def __init__(
        self,
        window_size: int = US_WINDOW_SIZE,
        num_channels: int = NUM_US_CHANNELS,
        thread_safe: bool = False,
    ):
        self.window_size = window_size
        self.num_channels = num_channels
        self.thread_safe = thread_safe

        # Create circular buffer for each channel
        self.buffers = [deque(maxlen=window_size) for _ in range(num_channels)]

        # Optional lock for thread safety
        self._lock = threading.Lock() if thread_safe else None

    def _acquire_lock(self):
        """Context manager for optional locking."""
        if self._lock is not None:
            return self._lock
        # Return a dummy context manager if no lock
        return _DummyLock()

    def add_sample_to_channel(self, us_data: np.ndarray, channel_id: int):
        """
        Add ultrasound packet to a specific channel.

        Appends all samples from the packet to the specified channel's
        circular buffer. Old samples are automatically discarded when
        the buffer reaches window_size.

        Parameters
        ----------
        us_data : np.ndarray
            Ultrasound samples from one packet, typically shape (397,)
        channel_id : int
            Channel ID (0 to num_channels-1), directly from tx_rx_id signal

        Raises
        ------
        ValueError
            If channel_id is out of range
        """
        if not 0 <= channel_id < self.num_channels:
            raise ValueError(
                f"channel_id must be 0-{self.num_channels - 1}, got {channel_id}"
            )

        with self._acquire_lock():
            # Add all samples to the channel's circular buffer
            for sample in us_data:
                self.buffers[channel_id].append(sample)

    def add_packet(self, us_data: np.ndarray, tx_rx_id: int):
        """
        Add ultrasound packet using tx_rx_id for channel determination.

        Convenience method that uses tx_rx_id directly as the channel ID.

        Parameters
        ----------
        us_data : np.ndarray
            Ultrasound samples from one packet
        tx_rx_id : int
            Transmit/receive configuration ID (0-3), directly identifies the channel
        """
        self.add_sample_to_channel(us_data, tx_rx_id)

    def is_ready(self) -> bool:
        """
        Check if all channels have full windows.

        Returns
        -------
        bool
            True if all channels have exactly window_size samples,
            False otherwise
        """
        with self._acquire_lock():
            return all(len(buf) == self.window_size for buf in self.buffers)

    def get_data(self) -> np.ndarray:
        """
        Get buffered data as a numpy array.

        Returns the current buffer contents as a 2D array suitable for
        neural network inference.

        Returns
        -------
        np.ndarray
            Array with shape (num_channels, window_size), dtype float32

        Note
        ----
        This returns a copy of the data. The buffer is not modified.
        """
        with self._acquire_lock():
            return np.array([list(buf) for buf in self.buffers], dtype=np.float32)

    def get_fill_status(self) -> str:
        """
        Get human-readable buffer fill status.

        Returns
        -------
        str
            Status string showing samples in each channel,
            e.g., "[397, 397, 256, 128] / 397"
        """
        with self._acquire_lock():
            fills = [len(buf) for buf in self.buffers]
            fills_str = ", ".join(f"{f:3d}" for f in fills)
            return f"[{fills_str}] / {self.window_size}"

    def get_fill_levels(self) -> list[int]:
        """
        Get the number of samples in each channel buffer.

        Returns
        -------
        list[int]
            List of sample counts for each channel
        """
        with self._acquire_lock():
            return [len(buf) for buf in self.buffers]

    def get_fill_percentage(self) -> float:
        """
        Get overall buffer fill percentage.

        Returns
        -------
        float
            Average fill percentage across all channels (0.0 to 1.0)
        """
        with self._acquire_lock():
            total_samples = sum(len(buf) for buf in self.buffers)
            max_samples = self.num_channels * self.window_size
            return total_samples / max_samples

    def clear(self):
        """Clear all channel buffers."""
        with self._acquire_lock():
            for buf in self.buffers:
                buf.clear()

    def is_cycle_complete(self, tx_rx_id: int) -> bool:
        """
        Check if a complete cycle of all channels has been received.

        A cycle is complete when we're back to channel 0, indicating
        all 4 configs have been received.

        Parameters
        ----------
        tx_rx_id : int
            Current transmit/receive configuration ID

        Returns
        -------
        bool
            True if tx_rx_id indicates we just completed a cycle
            (i.e., tx_rx_id == 0 and buffer is ready)
        """
        return tx_rx_id == 0 and self.is_ready()

    def __len__(self) -> int:
        """Return the number of channels."""
        return self.num_channels

    def __repr__(self) -> str:
        fills = self.get_fill_levels()
        ready = "ready" if self.is_ready() else "filling"
        return (
            f"USDataBuffer("
            f"channels={self.num_channels}, "
            f"window_size={self.window_size}, "
            f"fills={fills}, "
            f"status={ready})"
        )


class _DummyLock:
    """Dummy context manager for non-thread-safe mode."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
