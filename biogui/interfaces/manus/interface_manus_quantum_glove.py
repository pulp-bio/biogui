"""
Interface for the Manus Quantum Glove via ManusClient TCP stream.

Copyright 2025 ETH Zurich and University of Bologna

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---
Overview
--------
This interface decodes the TCP stream produced by ManusClient.exe (C++ app).

ManusClient acts as the TCP *client*: it connects to BioGUI which listens on
port 3333.  Each packet is 32 × float32 (128 bytes, little-endian) at ~120 Hz.

Packet layout (32 floats):
  [0:20]  ergo_right  — right-hand finger joint angles (radians)
              Thumb  (MCP spread, MCP stretch, PIP stretch, DIP stretch)
              Index  (same 4 DOF)
              Middle (same 4 DOF)
              Ring   (same 4 DOF)
              Pinky  (same 4 DOF)
  [20]    node_id     — always 0.0 (wrist/root node index; discarded)
  [21:24] hand_pos    — hand (wrist root) position x, y, z in metres (world)
  [24:28] hand_rot    — hand quaternion w, x, y, z (world orientation)
  [28:31] hand_scale  — node scale x, y, z (nominally [1,1,1]; discarded)
  [31]    manus_ts    — Manus Core timestamp in seconds from stream start

Coordinate system: Z-up, X-positive, right-handed, 1 unit = 1 m.

Timestamp details
-----------------
manus_ts is derived from the `publishTime` field that Manus Core stamps onto
each raw-skeleton frame at the moment it is generated.  The C++ client
converts it to seconds (supporting both timecode mode and wall-clock ms mode)
and subtracts the first-frame time, so the stream always starts at 0.0 s.
This is a **Core-side clock**, independent of the host PC, making it suitable
for cross-stream synchronisation via an external trigger.

Usage
-----
1. Launch BioGUI and add a TCP Socket data source on port 3333.
2. Select this interface.
3. Run ManusClient.exe — it connects and begins streaming automatically.
4. Stop acquisition in BioGUI; it sends 'S' to ManusClient for clean shutdown.
"""

import numpy as np

# Packet constants
SAMPLE_RATE = 120  # Hz (ManusClient targets 120 sps)
PACKET_SIZE = 128  # 32 × float32
N_ERGO_CH = 20     # right-hand finger ergonomics channels
N_POS_CH = 3       # hand position channels (x, y, z)
N_ROT_CH = 4       # hand rotation channels (w, x, y, z)

packetSize: int = PACKET_SIZE
"""Fixed-size packet: 32 floats × 4 bytes = 128 bytes.  No header/trailer byte."""

startSeq: list = []
"""No start command needed: ManusClient starts streaming as soon as TCP connects."""

stopSeq: list = [b"S"]
"""Send ASCII 'S' to tell ManusClient to shut down gracefully."""

sigInfo: dict = {
    "ergo_right": {"fs": SAMPLE_RATE, "nCh": N_ERGO_CH},
    "hand_pos":   {"fs": SAMPLE_RATE, "nCh": N_POS_CH},
    "hand_rot":   {"fs": SAMPLE_RATE, "nCh": N_ROT_CH},
    "manus_ts":   {"fs": SAMPLE_RATE, "nCh": 1},
}
"""
Signal metadata:

ergo_right (20 ch, 120 Hz)  — finger joint angles in radians
    Channel layout (0-indexed):
      0  Thumb  MCP spread    8  Middle MCP spread   16  Pinky MCP spread
      1  Thumb  MCP stretch   9  Middle MCP stretch  17  Pinky MCP stretch
      2  Thumb  PIP stretch  10  Middle PIP stretch  18  Pinky PIP stretch
      3  Thumb  DIP stretch  11  Middle DIP stretch  19  Pinky DIP stretch
      4  Index  MCP spread   12  Ring   MCP spread
      5  Index  MCP stretch  13  Ring   MCP stretch
      6  Index  PIP stretch  14  Ring   PIP stretch
      7  Index  DIP stretch  15  Ring   DIP stretch

    MCP = Metacarpophalangeal (knuckle), PIP = Proximal Interphalangeal,
    DIP = Distal Interphalangeal.
    Spread = abduction/adduction;  Stretch = flexion/extension.

hand_pos (3 ch, 120 Hz)  — wrist-root position [x, y, z] in metres, world space
hand_rot (4 ch, 120 Hz)  — wrist-root orientation quaternion [w, x, y, z]
manus_ts (1 ch, 120 Hz)  — Core-side elapsed time in seconds from stream start
"""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Decode a 128-byte Manus packet into signals.

    Parameters
    ----------
    data : bytes
        Exactly 128 bytes from the TCP stream (one ManusClient frame).

    Returns
    -------
    dict[str, np.ndarray]
        Each value has shape (nSamp, nCh) = (1, nCh), dtype float32.

    Raises
    ------
    ValueError
        If the packet length is not 128 bytes.
    """
    if len(data) != PACKET_SIZE:
        raise ValueError(
            f"Invalid Manus packet size: expected {PACKET_SIZE} bytes, got {len(data)}."
        )

    floats = np.frombuffer(data, dtype="<f4")  # 32 little-endian float32 values

    ergo_right = floats[0:20].reshape(1, N_ERGO_CH).astype(np.float32)
    # floats[20] = node index (always 0.0); not a useful signal
    hand_pos   = floats[21:24].reshape(1, N_POS_CH).astype(np.float32)
    hand_rot   = floats[24:28].reshape(1, N_ROT_CH).astype(np.float32)
    # floats[28:31] = node scale (nominally [1,1,1]); not exposed
    manus_ts   = floats[31:32].reshape(1, 1).astype(np.float32)

    return {
        "ergo_right": ergo_right,
        "hand_pos":   hand_pos,
        "hand_rot":   hand_rot,
        "manus_ts":   manus_ts,
    }
