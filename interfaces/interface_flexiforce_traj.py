"""
This module contains the FlexiForce interface for force data,
together with synthetic force trajectories.


Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import struct

import numpy as np

packetSize: int = 12
"""Number of bytes in each package."""

startSeq: list[bytes] = [b"="]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [b":"]
"""Sequence of commands to stop the board."""

sigInfo: dict = {"force": {"fs": 120, "nCh": 3}}
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
    force = np.zeros(shape=(1, 3), dtype=np.float32)

    # Read force data
    force[0, 0] = struct.unpack("<f", data[:4])[0]

    # Read trajectories
    force[0, 1:] = np.asarray(struct.unpack("<2f", data[4:]), dtype=np.float32)

    return {"force": force}
