import numpy as np

winLenS: float = 0.2
"""Length of the window to process (in s)."""

stepLenS: float = 0.02
"""Time (in s) between two consecutive processings."""


class ProcessFn:
    """Callable class to perform some operations on the input data and return the result in bytes."""

    def __init__(self) -> None:
        pass

    def __call__(self, data: dict[str, np.ndarray]) -> bytes:
        return b"".join(sig.tobytes() for sig in data.values())
