# Board Interface Development

BioGUI is designed to be easily extensible. Add a new interface\_<name>.py under biogui/platforms/<name>/ (one subfolder per device family, or colocate with an existing platform package such as WULPUS).

## Interface File Structure

An interface file is a Python module that must define specific variables and functions.

### Required Variables

- `packetSize`: `int`
  - The size in bytes of a single data packet received from the board.
- `startSeq`: `list[bytes | float]`
  - A sequence of bytes to send to the board to start acquisition. Floats are interpreted as delays in seconds between commands.
- `stopSeq`: `list[bytes | float]`
  - A sequence of bytes to send to stop acquisition.
- `sigInfo`: `dict`
  - A dictionary defining the signals. Keys are signal names, and values are dictionaries with `fs` (sampling rate) and `nCh` (number of channels).
  - Example: `{"emg": {"fs": 1000, "nCh": 8}, "acc": {"fs": 50, "nCh": 3}}`

### Required Functions

- `decodeFn(data: bytes) -> dict[str, np.ndarray]`
  - Takes a raw packet of bytes and returns a dictionary where keys match `sigInfo` and values are NumPy arrays of shape `(nSamples, nChannels)`.
  - It must return **every** key of `sigInfo` on **every** call. Use a zero-row array (`np.empty((0, nCh), dtype=...)`) for a signal that this particular packet carries nothing for. Give those placeholders the same dtype as the filled arrays: the recording writer locks each signal's dtype to the first array it sees.

## Signal Types

Each entry of `sigInfo` may carry an `extras` dictionary whose `type` key selects how the signal is filtered and plotted. It defaults to `"time-series"`.

| `type` | Preprocessing | Visualization |
| --- | --- | --- |
| `"time-series"` | Butterworth / notch filters, configurable per signal | Scrolling line plot, one trace per channel |
| `"ultrasound"` | None (filtering happens in the plot mode) | A-mode trace or M-mode depth-time heatmap |
| `"radar"` | None (range processing happens in the plot mode) | Range-time heatmap of FMCW radar frames |

`"ultrasound"` and `"radar"` signals also read their geometry from `extras`; see `MModePlotMode` and `RadarPlotMode` in [`biogui/views/plot_modes`](https://github.com/pulp-bio/biogui/blob/main/biogui/views/plot_modes) for the keys each one expects. A radar signal carries one flat stream of frames, so its `fs` is the sample rate of that stream (`frame_rate * samples_per_frame`), not the frame rate.

For a worked example of a multi-packet device, see `biogui/platforms/biogapultra/biogapultra_mmwave/`: it reassembles radar frames split across several BLE packets and exposes both the raw frames (`"radar"`) and derived waveforms (`"time-series"`) — phase and amplitude of the selected range bin, plus diagnostics.

Note the amplitude signal's floor (`radar.AMP_FLOOR_DB`). A dB-valued signal needs one: the magnitude it takes the logarithm of can legitimately reach exactly zero, and a single `-inf` or `-760 dB` sample sets the plot's y-range for the whole window, flattening everything real. Clamp to a value below the noise floor rather than to the smallest representable float.

## Two packet types on one link

When a device streams more than one sensor over the same connection, declare `packetSize` as a list of `(headerByte, size)` pairs instead of an `int`, and dispatch on `data[0]` inside `decodeFn`. Return the **full** signal set every time, leaving the other sensor's arrays empty.

Two interfaces do this with the mmWave radar:

| Interface | Packet types | Bus contention |
| --- | --- | --- |
| `biogapultra_exg_mmwave` | EEG `0x55` (211 B) + radar `0x60` (244 B) | both on SPI_A, arbitrated in firmware |
| `biogapultra_imu_mmwave` | IMU `0x56` (236 B) + radar `0x60` (244 B) | none — IMU is on I²C |

### Framing bytes and resync

A byte stream can lose sync — a dropped byte, or a port opened mid-stream. From then on every packet is cut across two real ones, the decoder rejects all of them, and the plots simply go empty with nothing logged.

Both the serial and TCP readers guard against this, but they need to know what a packet boundary looks like:

- **`packetSize` as a list of `(header, size)`** — the header table itself identifies boundaries. An unrecognised first byte is dropped and the search continues. Nothing extra to declare.
- **`packetSize` as an `int`** — a fixed stride is only trustworthy while aligned, so declare two module-level ints and the readers will verify each packet before emitting it:

```python
packetSize: int = 211
headerByte: int = 0x55   # data[0]
tailerByte: int = 0xAA   # data[packetSize - 1]
```

Both are optional and independent, but declaring only `headerByte` is weak: a payload byte matching it by coincidence is a false start, and the tailer landing where expected is what actually confirms alignment. Once realigned, the reader logs how many bytes it discarded, which is the signal that a link is lossy rather than dead.

The tailer is checked for fixed-size packets only — with a `(header, size)` table each packet type has its own trailer, and one `tailerByte` cannot describe them all.

Note how the decoding they share with the standalone radar interface lives in a plain module — `biogapultra_mmwave/radar.py` — imported with a normal absolute import. Only files named `interface_*.py` are treated as interfaces, so helper modules can sit alongside them, and putting the shared state in a class (rather than module globals) keeps several interfaces from interfering.

## Runtime-configurable interfaces

An interface can expose a settings dialog by defining a `platformConfig`. BioGUI opens it before acquisition, and again from the source's inline configure action. The contract is one callable:

```python
configureInterfaceModule(parent: QWidget, module: InterfaceModule) -> InterfaceModule | None
```

Return `None` to cancel, or a **completely rebuilt** `InterfaceModule` — settings usually affect `startSeq` (command bytes), `sigInfo` (`fs`, channel counts) and `decodeFn` together, so rebuilding all three keeps them consistent.

The radar interfaces show a compact way to do this. Settings live in a frozen dataclass, are stashed in `sigInfo[...]["extras"]` so the dialog can prefill from what is actually running, and `decodeFn` is a closure over a freshly constructed decoder — which also guarantees no stale phase-unwrap state survives a settings change. `radar.makeConfigureFn(title, buildModule)` turns a `(settings) -> InterfaceModule` builder into the callable above, so each of the three interfaces needs only its own builder.

This is deliberately lighter than WULPUS's approach in `biogapultra_exg_wulpus_pro`, which rebuilds `decodeFn` with `types.FunctionType` and a patched `__globals__`. A closure is enough when the decoder's state is already encapsulated in an object.

## Example: Dummy Interface

Here is a simplified example of an interface:

```python
import numpy as np

# Requirements
packetSize = 150
startSeq = [b'18']
stopSeq = [b'25']
sigInfo = {"test": {"fs": 100, "nCh": 1}}

def decodeFn(data):
    # Process 'data' and return signals
    val = np.frombuffer(data, dtype=np.int16)
    return {"test": val.reshape(-1, 1)}
```

## Tips for Development

- Look at existing files (e.g. biogui/platforms/dummy/interface_dummy.py) for reference.
- Ensure the sampling rates (`fs`) in `sigInfo` accurately reflect the board's output for correct visualization.
