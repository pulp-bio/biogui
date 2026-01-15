# Board Interface Development
BioGUI is designed to be easily extensible. You can support new acquisition boards by creating a new interface file in the `interfaces/` directory.

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
- Look at existing files in `interfaces/` (e.g., `interface_dummy.py`) for reference.
- Ensure the sampling rates (`fs`) in `sigInfo` accurately reflect the board's output for correct visualization.
