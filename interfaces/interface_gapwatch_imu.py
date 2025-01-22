"""
This module contains the GAPWatch interface for IMU.


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

import numpy as np

packetSize: int = 72
"""Number of bytes in each package."""

startSeq: list[bytes] = [b"="]
"""Sequence of commands to start the device."""

stopSeq: list[bytes] = [b":"]
"""Sequence of commands to stop the device."""

sigInfo: dict = {"imu": {"fs": 104, "nCh": 3}, "angle": {"fs": 104, "nCh": 3}}
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
    imu = np.frombuffer(data[:36], dtype=np.float32).reshape(3, 3)

    angle = np.zeros(shape=(3, 3), dtype=np.float32)
    angle[:, 0] = np.frombuffer(data[36:48], dtype=np.float32)
    angle[:, 1] = np.frombuffer(data[48:60], dtype=np.float32)
    angle[:, 2] = np.frombuffer(data[60:], dtype=np.float32)

    return {"imu": imu, "angle": angle}
