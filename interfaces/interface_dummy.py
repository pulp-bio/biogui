"""
This module contains an example interface for dummy signals.


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

packetSize: int = 0
"""Number of bytes in each package."""

startSeq: list[bytes] = []
"""Sequence of commands to start the device."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the device."""

sigInfo: dict = {"sig1": {"fs": 128, "nCh": 4}, "sig2": {"fs": 51.2, "nCh": 2}}
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
