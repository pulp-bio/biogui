# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Signal configuration and packet format definitions.

Handles decoding of data packets from BioGUI.

IMPORTANT: Signals are forwarded from BioGUI in ALPHABETICAL ORDER!
"""

from dataclasses import dataclass

import numpy as np

from .config import (
    NUM_ACQUISITION_NUMBER_CHANNELS,
    NUM_IMU_CHANNELS,
    NUM_TX_RX_ID_CHANNELS,
    NUM_US_SAMPLES,
)

# =============================================================================
# Data Types
# =============================================================================

DTYPE_US = np.int16
DTYPE_IMU = np.int16
DTYPE_ACQUISITION_NUMBER = np.uint16
DTYPE_TX_RX_ID = np.uint8


# =============================================================================
# Signal Definitions
# =============================================================================


@dataclass
class SignalInfo:
    """Information about a signal in a packet."""

    name: str
    num_samples: int  # Samples per frame
    num_channels: int
    dtype: type

    @property
    def bytes_per_frame(self) -> int:
        """Calculate bytes per frame."""
        return self.num_samples * self.num_channels * np.dtype(self.dtype).itemsize

    @property
    def total_samples(self) -> int:
        """Total number of samples (samples × channels)."""
        return self.num_samples * self.num_channels


@dataclass
class PacketFormat:
    """
    Packet format definition.

    Signals are stored in alphabetical order to match BioGUI forwarding.
    """

    signals: list[SignalInfo]

    def __post_init__(self):
        """Ensure signals are sorted alphabetically."""
        self.signals = sorted(self.signals, key=lambda s: s.name)

    @property
    def packet_size(self) -> int:
        """Calculate total bytes per packet."""
        return sum(sig.bytes_per_frame for sig in self.signals)

    def get_signal(self, name: str) -> SignalInfo:
        """Get signal info by name."""
        for sig in self.signals:
            if sig.name == name:
                return sig
        raise KeyError(f"Signal '{name}' not found in packet format")

    def decode(self, packet: bytes) -> dict[str, np.ndarray]:
        """
        Decode packet into dictionary of signals.

        Parameters
        ----------
        packet : bytes
            Raw packet data

        Returns
        -------
        dict[str, np.ndarray]
            Dictionary mapping signal names to numpy arrays

        Raises
        ------
        ValueError
            If packet size doesn't match expected size
        """
        if len(packet) != self.packet_size:
            raise ValueError(
                f"Invalid packet size: expected {self.packet_size} bytes, " f"got {len(packet)}"
            )

        result = {}
        offset = 0

        for sig_info in self.signals:
            # Extract bytes for this signal
            sig_bytes = packet[offset : offset + sig_info.bytes_per_frame]

            # Decode based on data type
            sig_data = np.frombuffer(sig_bytes, dtype=sig_info.dtype)

            # Reshape if multi-channel
            if sig_info.num_channels > 1:
                sig_data = sig_data.reshape(sig_info.num_samples, sig_info.num_channels)
                # Flatten to 1D: [sample0_ch0, sample0_ch1, ..., sample1_ch0, ...]
                sig_data = sig_data.flatten()

            result[sig_info.name] = sig_data
            offset += sig_info.bytes_per_frame

        return result

    def print_info(self):
        """Print information about this packet format."""
        print("=" * 70)
        print("WULPUS Packet Format")
        print("=" * 70)
        print(f"Signal order (alphabetical): {[s.name for s in self.signals]}")
        print(f"Total packet size: {self.packet_size} bytes")
        print()
        print("Signal breakdown:")
        print("-" * 70)

        for sig_info in self.signals:
            print(
                f"  {sig_info.name:15s}: "
                f"{sig_info.num_samples:3d} samples × "
                f"{sig_info.num_channels} ch × "
                f"{np.dtype(sig_info.dtype).itemsize} bytes = "
                f"{sig_info.bytes_per_frame:4d} bytes "
            )

        print("=" * 70)


# =============================================================================
# WULPUS Packet Format Definition
# =============================================================================

# Standard WULPUS packet format (acquisition_number, imu, tx_rx_id, ultrasound - alphabetically sorted)
WULPUS_PACKET_FORMAT = PacketFormat(
    signals=[
        SignalInfo(
            name="acquisition_number",
            num_samples=1,
            num_channels=NUM_ACQUISITION_NUMBER_CHANNELS,
            dtype=DTYPE_ACQUISITION_NUMBER,
        ),
        SignalInfo(
            name="imu",
            num_samples=1,
            num_channels=NUM_IMU_CHANNELS,
            dtype=DTYPE_IMU,
        ),
        SignalInfo(
            name="tx_rx_id",
            num_samples=1,
            num_channels=NUM_TX_RX_ID_CHANNELS,
            dtype=DTYPE_TX_RX_ID,
        ),
        SignalInfo(
            name="ultrasound",
            num_samples=NUM_US_SAMPLES,
            num_channels=1,
            dtype=DTYPE_US,
        ),
    ]
)

# Legacy compatibility: individual values
PACKET_SIZE = WULPUS_PACKET_FORMAT.packet_size
US_BYTES = WULPUS_PACKET_FORMAT.get_signal("ultrasound").bytes_per_frame


# =============================================================================
# Convenience Functions
# =============================================================================


def decode_packet(packet: bytes) -> dict[str, np.ndarray]:
    """
    Decode packet using the standard WULPUS packet format.

    Parameters
    ----------
    packet : bytes
        Raw packet data

    Returns
    -------
    dict[str, np.ndarray]
        Dictionary mapping signal names to numpy arrays:
        - acquisition_number: scalar value (uint16)
        - imu: shape (3,) [ax, ay, az] (int16)
        - tx_rx_id: scalar value (uint8)
        - ultrasound: shape (397,) (int16)
    """
    return WULPUS_PACKET_FORMAT.decode(packet)
