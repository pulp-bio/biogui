# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This module contains an example interface for dummy signals.
"""

import numpy as np

FS_DICT = {
    200: 0x01,
    500: 0x02,
    1000: 0x03,
}
GAIN_DICT = {
    1: 0x00,
    2: 0x10,
    4: 0x20,
    8: 0x30,
}
"""Dummy protocol: the script excepts a start command comprising:
- 1 byte: sampling frequency code for sig1;
- 1 byte: gain code for sig1;
- 1 byte: sampling frequency code for sig2;
- 1 byte: gain code for sig2;
- 1 byte: start command (b':').
The script will then generate signals accordingly.
"""

FS1 = 200
GAIN1 = 1
FS2 = 1000
GAIN2 = 4
N_SAMP1 = FS1 // 50
N_SAMP2 = FS2 // 50
"""Dummy signal parameters."""

packetSize: int = 4 * (4 * N_SAMP1 + 2 * N_SAMP2)
"""Number of bytes in each package."""

startSeq: list[bytes | float] = [
    bytes([FS_DICT[FS1], GAIN_DICT[GAIN1]]),
    0.05,
    bytes([FS_DICT[FS2], GAIN_DICT[GAIN2]]),
    0.05,
    b":",
]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = [b"="]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {"sig1": {"fs": FS1, "nCh": 4}, "sig2": {"fs": FS2, "nCh": 2}}
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
    sig1 = dataTmp[: N_SAMP1 * 4].reshape(N_SAMP1, 4)
    sig2 = dataTmp[N_SAMP1 * 4 :].reshape(N_SAMP2, 2)

    return {"sig1": sig1, "sig2": sig2}
