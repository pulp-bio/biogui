"""This module contains the decode function for sEMG from BioWolf.


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
    """Function to decode the binary data received from BioWolf into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    Sequence of ndarray
        Sequence of corresponding signals with shape (nSamp, nCh).
    """
    nSamp = 5
    nCh = 16

    # ADC parameters
    vRefADC = 2.5
    gainADC = 6.0

    dataTmp = bytearray(
        [x for i, x in enumerate(data) if i not in (0, 1, 242)]
    )  # discard header and footer

    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataTmp) // 3):
        preFix = 255 if dataTmp[pos] > 127 else 0
        dataTmp.insert(pos, preFix)
        pos += 4
    dataRef = np.asarray(struct.unpack(f">{pos}i", dataTmp), dtype=np.int32)

    # Reshape and convert ADC readings to uV
    dataRef = dataRef.reshape(nSamp, nCh)
    dataRef = dataRef * (vRefADC / gainADC / 2**24)  # V
    dataRef *= 1_000_000  # uV
    dataRef = dataRef.astype("float32")

    return [dataRef]
