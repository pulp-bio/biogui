"""
Shared utility functions for BioBridge middleware.

Centralizes common operations to avoid code duplication.
"""

from .config import (
    EXTENSION_MAX,
    FLEXION_MAX,
    PRONATION_MAX,
    SUPINATION_MAX,
)

# =============================================================================
# Clamping Functions
# =============================================================================


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to the range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def clamp01(value: float) -> float:
    """Clamp a value to the range [0.0, 1.0]."""
    return clamp(value, 0.0, 1.0)


def clamp_flexion(angle: float) -> float:
    """
    Clamp flexion/extension angle to valid range.
    """
    return clamp(angle, FLEXION_MAX, EXTENSION_MAX)


def clamp_supination(angle: float) -> float:
    """
    Clamp supination angle to valid range.
    """
    return clamp(angle, PRONATION_MAX, SUPINATION_MAX)


# =============================================================================
# Network Utilities
# =============================================================================


def recv_exact(conn, n: int) -> bytes:
    """
    Receive exactly n bytes from a socket connection.

    Keeps reading until all requested bytes are received or
    the connection is closed.

    Parameters
    ----------
    conn : socket
        Socket connection
    n : int
        Number of bytes to receive

    Returns
    -------
    bytes
        Received data of exactly n bytes

    Raises
    ------
    ConnectionError
        If connection is closed before receiving all bytes
    """
    data = bytearray()
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data.extend(chunk)
    return bytes(data)


# =============================================================================
# Array Utilities
# =============================================================================


def softmax(logits):
    """
    Compute softmax probabilities from logits.

    Parameters
    ----------
    logits : array-like
        Raw model outputs (logits)

    Returns
    -------
    np.ndarray
        Softmax probabilities that sum to 1
    """
    import numpy as np

    exp_logits = np.exp(logits - np.max(logits))
    return exp_logits / exp_logits.sum()
