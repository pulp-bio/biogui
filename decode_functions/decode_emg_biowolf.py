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
    gainScaleFactor = 2.38125854276502e-08
    vScaleFactor = 1_000_000

    # Bytes to floats
    dataRef = np.zeros(shape=(nSamp, nCh), dtype="uint32")
    dataTmp = [
        x for i, x in enumerate(data) if i not in (0, 1, 242)
    ]  # discard header and footer
    for k in range(nSamp):
        for i in range(nCh):
            dataRef[k, i] = (
                dataTmp[k * 48 + (3 * i)] * 256**3
                + dataTmp[k * 48 + (3 * i) + 1] * 256**2
                + dataTmp[k * 48 + (3 * i) + 2] * 256
            )
    dataRef = dataRef.view("int32").astype("float32")
    dataRef = dataRef / 256 * gainScaleFactor * vScaleFactor
    dataRef = dataRef.astype("float32")

    return [dataRef]
