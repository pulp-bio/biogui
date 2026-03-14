# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This module contains the MANUS interface for joint data,
together with synthetic angle trajectories.

"""

import struct

import numpy as np

packetSize: int = 12
"""Number of bytes in each package."""

startSeq: list[bytes | float] = [b":"]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = [b"S"]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {
    "angle": {
        "fs": 120,
        "nCh": 3,
        "signal_type": {"type": "time-series"},
    }
}
"""Dictionary containing the signals information."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Function to decode the binary data received from the device into signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    dict of (str: ndarray)
        Dictionary containing the signal data packets, each with shape (nSamp, nCh);
        the keys must match with those of the "sigInfo" dictionary.
    """
    angle = np.zeros(shape=(1, 3), dtype=np.float32)

    # Read angle data
    angle[:, 0] = np.asarray(struct.unpack("<f", data[:4]))

    # Read trajectories
    angle[:, 1:] = np.asarray(struct.unpack("<2f", data[4:]))

    return {"angle": angle}
