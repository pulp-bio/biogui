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
    # nSamp = 40
    # nCh = 2
 
    # # ADC parameters
    # vRef = 2.5
    # gain = 6.0
    # nBit = 24

    ecgBytes = bytearray(data[:128])
    bioZBytes = bytearray(data[128:])
 
    # Convert 24-bit to 32-bit integer
    # pos = 0
    # for _ in range(len(dataTmp) // 3):
    #     preFix = 255 if dataTmp[pos] > 127 else 0
    #     dataTmp.insert(pos, preFix)
    #     pos += 4
    ecg = np.asarray(struct.unpack(">32i", ecgBytes), dtype="int32").reshape(-1, 1)
    bioZ = np.asarray(struct.unpack(">8i", bioZBytes), dtype="int32").reshape(-1, 1)
 
    # Reshape and convert ADC readings to uV
    # emg = emg.reshape(nSamp, nCh)
    # emg = emg * (vRef / gain / 2**nBit)  # V
    # emg *= 1_000_000  # uV
    # emg = emg.astype("float32")
 
    return ecg, bioZ
