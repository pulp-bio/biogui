# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Shared decoding and configuration for the BioGAP-Ultra mmWave radar shield
(Infineon BGT60TR13C).

Used by the standalone radar interface and by the combined ExG + radar and
IMU + radar interfaces, so frame reassembly, 12-bit unpacking, pulse-phase
extraction and the settings dialog exist once.

## What the sensor measures

The chirp sweeps 58-63.5 GHz, so range resolution is c/2B = 27 mm and the eight
samples per chirp give five range bins covering 0-109 mm. That is deliberately
coarse: distance is not the measurement. Phase is. Phase advances 2*pi per
lambda/2 = 2.47 mm of target motion, so one radian is ~393 um and arterial skin
displacement (10-500 um) lands at 0.03-1.3 rad -- easily resolved.

The 32 chirps in a frame are *not* used for Doppler: 32 chirps span 511 us, which
gives a velocity resolution of ~4.8 m/s, thousands of times too coarse for pulse
motion. They are averaged coherently instead, which buys sqrt(32) ~ 5.7x
amplitude SNR against noise uncorrelated between chirps.

The frame geometry here must match the firmware's compiled-in register profile
(CONFIG_MMWAVE_CONF_*, see sensors/mmWave/mmWave_config.h). Changing the profile
in the firmware means changing NUM_CHIRPS / NUM_SAMPLES here too. The frame rate
is different: the firmware's profile sets a nominal value, but opcode 51 changes
it at runtime, so it lives in RadarSettings.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from biogui.platforms.biogapultra import connectivity_commands as _cmd

# =============================================================================
# Frame geometry - must match the firmware's register profile
# =============================================================================

NUM_CHIRPS = 32
NUM_SAMPLES = 8  # ADC samples per chirp
NUM_RX = 1  # active RX antennas

SAMPLES_PER_FRAME = NUM_CHIRPS * NUM_SAMPLES * NUM_RX
PACKED_FRAME_BYTES = (SAMPLES_PER_FRAME * 3) // 2

# Real FFT of NUM_SAMPLES samples: bin 0 is the residual DC term, the rest carry
# range information.
N_RANGE_BINS = NUM_SAMPLES // 2 + 1

# Chirp band
START_FREQ_HZ = 58.0e9
END_FREQ_HZ = 63.5e9

# ADC resolution, for the saturation readout
ADC_BITS = 12
ADC_MAX_CODE = (1 << ADC_BITS) - 1

# Lower bound for the amplitude readout, in dB.
#
# Bin magnitudes are in ADC counts after DC removal, so a frame that is exactly
# constant -- an all-zero FIFO, or a radar powered but not chirping, i.e. what a
# stall looks like -- has magnitude 0 and would take the logarithm to about
# -760 dB. A single such sample crushes the plot's autoscale against a real
# range of roughly 0 dB (noise) to 72 dB (full-scale target).
#
# Clamping cannot be at 1 count: coherent averaging over the chirps pushes the
# genuine noise floor below one LSB (around -7 dB), and that detail is worth
# keeping. -60 dB sits about 50 dB below the noise floor, so it discards nothing
# real while keeping the trace bounded.
AMP_FLOOR_DB = -60.0
_AMP_MAG_FLOOR = 10.0 ** (AMP_FLOOR_DB / 20.0)

_SPEED_OF_LIGHT = 299_792_458.0

# =============================================================================
# Adjustable settings
# =============================================================================

# Discrete IF gain steps the firmware accepts (register 0x12 lookup table)
VALID_IF_GAINS_DB = (18, 23, 28, 30, 33, 35, 38, 40, 43, 45, 48, 50, 55, 60)
# Frame rates the firmware has register values for (registers 0x06 and 0x2d)
VALID_FRAME_RATES = (25, 50, 100, 150, 200)
TX_POWER_RANGE = (0, 31)


@dataclass(frozen=True)
class RadarSettings:
    """
    Runtime-adjustable radar settings.

    The first three are sent to the firmware as BLE commands at start-up; the
    last two are host-side processing choices.
    """

    ifGainDb: int = 33
    """Receiver IF gain. Too low is noise-limited, too high clips the ADC."""

    txPower: int = 31
    """Transmit power level, 0-31. Trades SNR against power draw."""

    frameRate: int = 100
    """Frames per second, i.e. the sampling rate of the phase waveform."""

    rangeBin: int = 1
    """Range bin the primary phase waveform is taken from. Bin 0 is the residual
    DC term, so bin 1 is the first with range information and the usual choice
    for a sensor worn against the skin."""

    rxIndex: int = 0
    """RX antenna used. Every shipped register profile enables only one."""

    def validated(self) -> "RadarSettings":
        """Clamp/snap every field to something the firmware will accept."""
        gain = min(VALID_IF_GAINS_DB, key=lambda g: abs(g - self.ifGainDb))
        rate = min(VALID_FRAME_RATES, key=lambda r: abs(r - self.frameRate))
        return replace(
            self,
            ifGainDb=gain,
            frameRate=rate,
            txPower=int(np.clip(self.txPower, *TX_POWER_RANGE)),
            rangeBin=int(np.clip(self.rangeBin, 0, N_RANGE_BINS - 1)),
            rxIndex=int(np.clip(self.rxIndex, 0, NUM_RX - 1)),
        )


DEFAULT_SETTINGS = RadarSettings()

# =============================================================================
# Packet layout (see Firmware/docs/BLE_PACKET_STRUCTURE.md section 3.6)
# =============================================================================

PACKET_SIZE = 244
HEADER_BYTE = 0x60
TRAILER_BYTE = 0x61
PAYLOAD_OFFSET = 7
PAYLOAD_SIZE = PACKET_SIZE - 8  # 7 leading + 1 trailing framing byte

# A gap this large in the device timestamp means the stream restarted, so the
# accumulated phase unwrapping is no longer meaningful.
TIMESTAMP_GAP_RESET_US = 1_000_000

# =============================================================================
# BLE opcodes
# =============================================================================
# Aliases of the shared table, which mirrors ble/ble_commands.h. The radar's
# own sequences read as radar.CMD_*, but the numbers live in exactly one place:
# a second copy here once drifted from it (START became 40, i.e.
# STOP_PPG_STREAMING), and because that opcode's firmware case body is compiled
# out the radar simply never started, with nothing logged either side.

CMD_START = _cmd.START_MMWAVE_STREAMING
CMD_STOP = _cmd.STOP_MMWAVE_STREAMING
CMD_CONFIGURE = _cmd.CONFIGURE_MMWAVE
CMD_TURN_OFF = _cmd.TURN_OFF_MMWAVE
CMD_TURN_ON = _cmd.TURN_ON_MMWAVE
CMD_SET_IF_GAIN = _cmd.CHANGE_IFGAIN_MMWAVE
CMD_SET_TX_POWER = _cmd.CHANGE_TXPOWER_MMWAVE
CMD_SET_FPS = _cmd.CHANGE_FPS_MMWAVE

_WINDOW = np.hanning(NUM_SAMPLES)


def rangeAxisMm() -> np.ndarray:
    """
    Nominal range of each FFT bin, in millimetres.

    Bin spacing is the range resolution c/(2B). This assumes the ADC window
    covers the configured sweep; if the profile samples only part of the ramp the
    true spacing is larger and these labels are optimistic. It does not affect
    the phase measurement, only the axis annotation.
    """
    bandwidth = abs(END_FREQ_HZ - START_FREQ_HZ)
    if bandwidth <= 0:
        return np.arange(N_RANGE_BINS, dtype=np.float64)
    return np.arange(N_RANGE_BINS) * (_SPEED_OF_LIGHT / (2.0 * bandwidth) * 1e3)


def powerOnAndConfigureSeq(settings: RadarSettings = DEFAULT_SETTINGS) -> list[bytes | float]:
    """
    Commands that power the radar and write its configuration, but do not start
    streaming. The radar must be powered and configured before it can stream, and
    a power cycle invalidates the configuration.
    """
    s = settings.validated()
    return [
        bytes([CMD_TURN_ON]),
        0.05,
        bytes([CMD_SET_IF_GAIN, s.ifGainDb]),
        0.02,
        bytes([CMD_SET_TX_POWER, s.txPower]),
        0.02,
        bytes([CMD_SET_FPS, s.frameRate]),
        0.02,
        bytes([CMD_CONFIGURE]),
        0.05,
    ]


def stopAndPowerOffSeq() -> list[bytes | float]:
    """Commands that stop radar streaming and cut its power."""
    return [bytes([CMD_STOP]), 0.05, bytes([CMD_TURN_OFF])]


def sigInfoDict(
    settings: RadarSettings = DEFAULT_SETTINGS, prefix: str = "mmwave"
) -> dict:
    """
    Signal definitions for the radar.

    ``_phase`` is the pulse waveform from the selected range bin -- the one to
    plot. ``_amp`` is that same bin's magnitude in dB: phase says how the target
    moved, amplitude says whether there was a target to believe, so a phase
    excursion during an amplitude dropout is an artefact rather than motion.
    ``_phase_bins`` carries every bin's unwrapped phase so a different bin can be
    chosen after the fact without re-recording. ``_raw`` keeps the ADC samples in
    frame order, typed ``"radar"`` so it gets the range-time heatmap; its ``fs``
    is the rate of the flattened sample stream, not the frame rate, so the
    heatmap's time axis comes out right. ``_level`` is the per-frame ADC min/max,
    which is the only way to see the IF gain clipping.

    Both ``_phase`` and ``_amp`` are plotted by default; the diagnostic signals
    are not, though they stay selectable and are recorded regardless.
    """
    s = settings.validated()
    fps = float(s.frameRate)

    return {
        f"{prefix}_phase": {
            "fs": fps,
            "nCh": 1,
            "extras": {"type": "time-series"},
        },
        f"{prefix}_amp": {
            "fs": fps,
            "nCh": 1,
            "extras": {"type": "time-series"},
        },
        f"{prefix}_phase_bins": {
            "fs": fps,
            "nCh": N_RANGE_BINS,
            "extras": {"type": "time-series", "plotByDefault": False},
        },
        f"{prefix}_raw": {
            "fs": fps * SAMPLES_PER_FRAME,
            "nCh": 1,
            "extras": {
                "type": "radar",
                "num_chirps": NUM_CHIRPS,
                "num_samples": NUM_SAMPLES,
                "num_rx": NUM_RX,
                "rx_index": s.rxIndex,
                "range_bin": s.rangeBin,
                "frame_rate": fps,
                "start_freq_hz": START_FREQ_HZ,
                "end_freq_hz": END_FREQ_HZ,
                "if_gain_db": s.ifGainDb,
                "tx_power": s.txPower,
                "adc_bits": ADC_BITS,
            },
        },
        f"{prefix}_level": {
            "fs": fps,
            "nCh": 2,
            "extras": {"type": "time-series", "plotByDefault": False},
        },
        f"{prefix}_timestamp": {
            "fs": fps,
            "nCh": 1,
            "extras": {"type": "time-series", "plotByDefault": False},
        },
        f"{prefix}_sync": {
            "fs": fps,
            "nCh": 1,
            "extras": {"type": "time-series", "plotByDefault": False},
        },
    }


def settingsFromSigInfo(
    sigInfo: dict, prefix: str = "mmwave"
) -> RadarSettings:
    """
    Recover the settings a module was built with, for prefilling the dialog.

    They are stashed in the ``_raw`` signal's ``extras`` by :func:`sigInfoDict`,
    which survives the InterfaceModule rebuild that applying the dialog performs.
    Falls back to the defaults for anything missing.
    """
    extras = sigInfo.get(f"{prefix}_raw", {}).get("extras", {})
    return RadarSettings(
        ifGainDb=int(extras.get("if_gain_db", DEFAULT_SETTINGS.ifGainDb)),
        txPower=int(extras.get("tx_power", DEFAULT_SETTINGS.txPower)),
        frameRate=int(extras.get("frame_rate", DEFAULT_SETTINGS.frameRate)),
        rangeBin=int(extras.get("range_bin", DEFAULT_SETTINGS.rangeBin)),
        rxIndex=int(extras.get("rx_index", DEFAULT_SETTINGS.rxIndex)),
    ).validated()


def emptyResult(prefix: str = "mmwave") -> dict[str, np.ndarray]:
    """
    "Nothing to report" arrays for the radar signals.

    decodeFn must return every signal on every call, and the recording writer
    locks each signal's dtype to the first array it sees, so these placeholders
    must carry the same dtypes as the filled arrays.
    """
    return {
        f"{prefix}_phase": np.empty((0, 1), dtype=np.float32),
        f"{prefix}_phase_bins": np.empty((0, N_RANGE_BINS), dtype=np.float32),
        f"{prefix}_amp": np.empty((0, 1), dtype=np.float32),
        f"{prefix}_raw": np.empty((0, 1), dtype=np.uint16),
        f"{prefix}_level": np.empty((0, 2), dtype=np.uint16),
        f"{prefix}_timestamp": np.empty((0, 1), dtype=np.uint32),
        f"{prefix}_sync": np.empty((0, 1), dtype=np.uint8),
    }


def unpack12Bit(packed: bytes, numSamples: int) -> np.ndarray:
    """
    Unpack 12-bit ADC samples, two per three bytes.

    Parameters
    ----------
    packed : bytes
        Packed payload, at least ``ceil(numSamples / 2) * 3`` bytes long.
    numSamples : int
        Number of samples to extract.

    Returns
    -------
    ndarray
        Samples of shape (numSamples,), dtype uint16.
    """
    numPairs = (numSamples + 1) // 2
    raw = np.frombuffer(packed, dtype=np.uint8, count=numPairs * 3)

    b0 = raw[0::3].astype(np.uint16)
    b1 = raw[1::3].astype(np.uint16)
    b2 = raw[2::3].astype(np.uint16)

    out = np.empty(numPairs * 2, dtype=np.uint16)
    out[0::2] = (b0 << 4) | (b1 >> 4)
    out[1::2] = ((b1 & 0x0F) << 8) | b2

    return out[:numSamples]


def rangeSpectra(samples: np.ndarray, rxIndex: int = 0) -> np.ndarray:
    """
    Chirp-averaged complex range spectrum of one frame.

    The per-chirp DC offset is removed, a Hann window is applied along the
    samples of each chirp and a range FFT is taken. The resulting complex spectra
    are averaged over the chirps -- averaging complex values rather than
    magnitudes is what suppresses noise uncorrelated between chirps and makes
    sub-millimetre displacement visible in the phase.

    Parameters
    ----------
    samples : ndarray
        Unpacked frame of ``SAMPLES_PER_FRAME`` samples.
    rxIndex : int
        RX antenna to use.

    Returns
    -------
    ndarray
        Complex spectrum of shape (N_RANGE_BINS,).
    """
    cube = samples.astype(np.float64).reshape(NUM_CHIRPS, NUM_SAMPLES, NUM_RX)
    chirps = cube[:, :, rxIndex]
    chirps = chirps - chirps.mean(axis=1, keepdims=True)
    return np.fft.rfft(chirps * _WINDOW, axis=1).mean(axis=0)


class RadarDecoder:
    """
    Reassembles chunked radar packets and turns complete frames into signals.

    Holds the frame-reassembly and per-bin phase-unwrapping state, so an
    interface module just forwards packets to :meth:`feed`. Instantiating a new
    decoder resets everything, which keeps state from leaking between
    acquisitions and lets the settings dialog swap one in cleanly.
    """

    def __init__(
        self,
        settings: RadarSettings = DEFAULT_SETTINGS,
        prefix: str = "mmwave",
    ) -> None:
        self._settings = settings.validated()
        self._prefix = prefix
        self._chunks: list[bytes] = []
        self._currentTs: int | None = None
        self._expectedChunk = 0
        # Each bin unwraps independently: their phases are unrelated.
        self._prevPhase: np.ndarray | None = None
        self._phaseOffset = np.zeros(N_RANGE_BINS, dtype=np.float64)
        self._lastTs: int | None = None

    @property
    def settings(self) -> RadarSettings:
        return self._settings

    def _resetFrame(self) -> None:
        """Discard the partially reassembled frame."""
        self._chunks = []
        self._currentTs = None
        self._expectedChunk = 0

    def _unwrapPhases(self, phases: np.ndarray) -> np.ndarray:
        """
        Unwrap every bin's phase against its own previous value.

        scipy's ``unwrap`` needs the whole series, so a running per-bin offset is
        tracked instead: whenever a wrapped phase jumps by more than pi, that
        bin's offset absorbs a full turn.
        """
        if self._prevPhase is None:
            self._prevPhase = phases.copy()
            return phases

        delta = phases - self._prevPhase
        self._phaseOffset -= 2 * np.pi * (delta > np.pi)
        self._phaseOffset += 2 * np.pi * (delta < -np.pi)

        self._prevPhase = phases.copy()
        return phases + self._phaseOffset

    def _resetPhase(self) -> None:
        self._prevPhase = None
        self._phaseOffset = np.zeros(N_RANGE_BINS, dtype=np.float64)

    def feed(self, data: bytes) -> dict[str, np.ndarray]:
        """
        Consume one radar packet.

        Parameters
        ----------
        data : bytes
            A single packet, expected to be PACKET_SIZE bytes with the radar
            header and trailer.

        Returns
        -------
        dict of {str : ndarray}
            The radar signals. All empty until a frame is complete, which
            happens on its last chunk.
        """
        p = self._prefix
        result = emptyResult(p)

        if (
            len(data) < PACKET_SIZE
            or data[0] != HEADER_BYTE
            or data[PACKET_SIZE - 1] != TRAILER_BYTE
        ):
            self._resetFrame()
            return result

        tsPacked = int.from_bytes(data[1:5], "big")
        timestamp = tsPacked & ~0x01
        syncState = tsPacked & 0x01
        chunk = data[5]
        totalChunks = data[6]

        if totalChunks == 0:
            self._resetFrame()
            return result

        if chunk == 0:
            # A new frame supersedes whatever was in progress
            self._chunks = []
            self._currentTs = timestamp
            self._expectedChunk = 0
        elif (
            self._currentTs is None
            or timestamp != self._currentTs
            or chunk != self._expectedChunk
        ):
            # Lost or out-of-order chunk: the frame cannot be reconstructed
            self._resetFrame()
            return result

        self._chunks.append(data[PAYLOAD_OFFSET : PAYLOAD_OFFSET + PAYLOAD_SIZE])
        self._expectedChunk += 1

        if chunk + 1 < totalChunks:
            return result

        payload = b"".join(self._chunks)
        self._resetFrame()

        if len(payload) < PACKED_FRAME_BYTES:
            return result

        # The last chunk is zero padded, so trim to the exact frame size
        samples = unpack12Bit(payload[:PACKED_FRAME_BYTES], SAMPLES_PER_FRAME)

        # A large jump in the device timestamp means the stream restarted; the
        # accumulated unwrapping offsets would otherwise carry over into it.
        if self._lastTs is not None and (
            timestamp < self._lastTs or timestamp - self._lastTs > TIMESTAMP_GAP_RESET_US
        ):
            self._resetPhase()
        self._lastTs = timestamp

        spectra = rangeSpectra(samples, self._settings.rxIndex)
        phases = self._unwrapPhases(np.angle(spectra))

        result[f"{p}_phase"] = np.array(
            [[phases[self._settings.rangeBin]]], dtype=np.float32
        )
        result[f"{p}_phase_bins"] = phases.astype(np.float32).reshape(1, -1)
        # Amplitude of the selected range bin in dB (20*log10 of magnitude),
        # which compresses the wide dynamic range of the return into something
        # readable next to the phase. Floored at AMP_FLOOR_DB so a degenerate
        # frame cannot take the logarithm to -760 dB and flatten the plot.
        val = np.abs(spectra[self._settings.rangeBin])
        amp_db = 20.0 * np.log10(max(float(val), _AMP_MAG_FLOOR))
        result[f"{p}_amp"] = np.array([[amp_db]], dtype=np.float32)
        result[f"{p}_raw"] = samples.reshape(-1, 1)
        result[f"{p}_level"] = np.array(
            [[samples.min(), samples.max()]], dtype=np.uint16
        )
        result[f"{p}_timestamp"] = np.array([[timestamp]], dtype=np.uint32)
        result[f"{p}_sync"] = np.array([[syncState]], dtype=np.uint8)

        return result
