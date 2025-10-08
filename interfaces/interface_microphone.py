"""
This module contains the interface for the system microphone audio source.

Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

Licensed under the Apache License, Version 2.0 (the \"License\");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an \"AS IS\" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import numpy as np
import struct
import time
# Number of bytes in each audio packet; must match the packetSize configured in MicrophoneConfigWidget
packetSize: int = 1920
"""Number of bytes in each package."""

# No explicit start/stop commands needed for live microphone streaming
startSeq: list[bytes] = []
"""Sequence of commands to start the device (none for microphone)."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the device (none for microphone)."""

# Signal information: audio stream with a default sample rate and channel count
sigInfo: dict = {"audio": {"fs": 48000, "nCh": 1}, "ts": {"fs": 25, "nCh": 1}}
"""Dictionary containing the signals information."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Decode raw PCM audio bytes into a numpy array.

    Parameters
    ----------
    data : bytes
        A packet of raw audio bytes.

    Returns
    -------
    dict of (str: ndarray)
        Dictionary containing the audio signal with shape (nSamp, nCh);
        values are normalized floats in [-1, 1].
    """
    # Interpret as little-endian 16-bit signed integers
    arr = np.frombuffer(data, dtype=np.int16)
    nCh = sigInfo["audio"]["nCh"]
    nSamp = arr.size // nCh
    audio = arr.reshape(nSamp, nCh).astype(np.float32) / np.iinfo(np.int16).max
    #add timestamp at reception
    ts = time.time()
    ts = np.asarray(ts, dtype=np.float64).reshape(-1,1)
    return {"audio": audio, "ts": ts}
