import struct

import numpy as np

winLenS: float = 0.5
"""Length of the window to process (in s)."""

stepLenS: float = 0.1
"""Time (in s) between two consecutive processings."""


def processFn(data: dict[str, np.ndarray]) -> bytes:
    """
    Function to perform some operations on the input data and return the result.

    Parameters
    ----------
    data : dict of (str: ndarray)
        Input data.

    Returns
    -------
    bytes
        Result of the operation in bytes.
    """
    avg = sum([d.mean() for d in data.values()]) / len(data)

    return struct.pack("<f", avg)
