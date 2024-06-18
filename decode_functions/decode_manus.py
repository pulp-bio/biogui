"""This module contains the decode function for sEMG from GAPWatch.


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
    """Function to decode the binary data received from GAPWatch into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    Sequence of ndarray
        Sequence of corresponding signals with shape (nSamp, nCh).
    """
    nSamp = 1
    nCh = 40

    joints = np.asarray(struct.unpack(f"<{nSamp * nCh}f", data), dtype="float32")

    # Reshape and convert ADC readings to uV
    joints = joints.reshape(nSamp, nCh)[:,:20]

    return [joints]
