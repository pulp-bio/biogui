"""This module contains the decode function for dummy signals.


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
from collections.abc import Sequence

import numpy as np


def decodeFn(data: bytes) -> Sequence[np.ndarray]:
    """Function to decode the binary data generated into two dummy signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    Sequence of ndarray
        Sequence of corresponding signals with shape (nSamp, nCh).
    """
    dataTmp = np.frombuffer(data, dtype="float32")
    nSamp1, nCh1 = 10, 4
    nSamp2, nCh2 = 4, 2
    sig1 = dataTmp[: nSamp1 * nCh1].reshape(nSamp1, nCh1)
    sig2 = dataTmp[nSamp1 * nCh1 :].reshape(nSamp2, nCh2)

    return [sig1, sig2]
