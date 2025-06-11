import numpy as np

winLenS: float = 0.05
"""Length of the window to process (in s)."""

stepLenS: float = 0.05
"""Time (in s) between two consecutive processings."""


class ProcessFn:
    """Callable class to perform some operations on the input data and return the result in bytes."""

    def __init__(self) -> None:
        pass

    def __call__(self, data: dict[str, np.ndarray]) -> bytes:
        return b"".join(sig.astype(np.float32).tobytes() for sig in data.values())
