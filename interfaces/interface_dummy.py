# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This module contains an example interface for dummy signals.
"""

import numpy as np

packetSize: int = 192
"""Number of bytes in each package."""

startSeq: list[bytes | float] = [b":"]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = [b"="]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {
    "sig1": {
        "fs": 128,
        "nCh": 4,
        "signal_type": {"type": "time-series"},
    },
    "sig2": {
        "fs": 51.2,
        "nCh": 2,
        "signal_type": {"type": "time-series"},
    },
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
    dataTmp = np.frombuffer(data, dtype=np.float32)
    nSamp1, nSamp2 = 10, 4
    sig1 = dataTmp[: nSamp1 * 4].reshape(nSamp1, 4)
    sig2 = dataTmp[nSamp1 * 4 :].reshape(nSamp2, 2)

    return {"sig1": sig1, "sig2": sig2}
