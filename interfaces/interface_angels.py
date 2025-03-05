"""
This module contains the ANGELS interface for PPG.


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

GAIN = 12


def createCommand(start: bool) -> list[bytes | float]:
    """Internal function to create start command."""
    if start:
        current = [20] * 16
        factorV0 = 7.26
        factorV2 = 2
        resistance = 33

        cmds = []

        # Set fs = 1kHz
        cmd1 = bytearray(10)
        cmd1[0] = ord("C")
        cmd1[1] = ord("M")
        cmd1[2] = ord("D")
        cmd1[3] = ord("8")
        cmds.append(bytes(cmd1))

        # Set DAC
        for i in range(16):
            cmd2 = bytearray(10)
            cmd2[0] = ord("C")
            cmd2[1] = ord("M")
            cmd2[2] = ord("D")
            cmd2[3] = ord("D")
            cmd2[4] = ord("1")
            cmd2[5] = i

            if i % 4 == 0:
                voltageDAC = factorV0 * resistance * current[i] / 1000
            else:
                voltageDAC = factorV2 * resistance * current[i] / 1000

            if i < 8:
                voltageDACfin = int(voltageDAC * 4096 / 5)
            else:
                voltageDACfin = int(voltageDAC * 4096 / 5)

            cmd2[6] = voltageDACfin // 256
            cmd2[7] = voltageDACfin % 256

            cmds.append(bytes(cmd2))
            cmds.append(0.025)

        # Start
        cmd3 = bytearray(10)
        cmd3[0] = ord("C")
        cmd3[1] = ord("M")
        cmd3[2] = ord("D")
        cmd3[3] = ord("1")
        cmds.append(bytes(cmd3))

        return cmds
    else:
        cmd = bytearray(10)
        cmd[0] = ord("C")
        cmd[1] = ord("M")
        cmd[2] = ord("D")
        cmd[3] = ord("2")

        return [bytes(cmd)]


packetSize: int = 15_364
"""Number of bytes in each package."""

startSeq: list[bytes | float] = createCommand(start=True)
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = createCommand(start=False)
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {"ppg": {"fs": 4096, "nCh": 2}}
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
    nSamp, nCh = 256, 15
    dataTmp = np.asarray(
        struct.unpack(f"<{nSamp * nCh}i", data[:-4]), dtype=np.float32
    ).reshape(nSamp, nCh)
    dataTmp *= 4.5 / 2**23

    ppg = dataTmp[:, 1:3]

    return {"ppg": ppg}
