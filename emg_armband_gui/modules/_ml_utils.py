"""This module contains utility functions for Machine Learning models.


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

from __future__ import annotations

import numpy as np
from scipy import signal


def waveformLength(data: np.ndarray, kernelSize: int) -> np.ndarray:
    """Compute the waveform length of a given signal.

    Parameters
    ----------
    data : ndarray
        Data with shape (nSamp,).
    kernelSize : int
        Size of the kernel.

    Returns
    -------
    ndarray
        Waveform length of the signal.
    """
    absDiff = np.abs(np.diff(data, prepend=0))
    kernel = np.ones(kernelSize)
    wl = signal.convolve(absDiff, kernel, mode="valid")
    return wl


def rootMeanSquared(data: np.ndarray, kernelSize: int) -> np.ndarray:
    """Compute the RMS of a given signal.

    Parameters
    ----------
    data : ndarray
        Data with shape (nSamp,).
    kernelSize : int
        Size of the kernel.

    Returns
    -------
    ndarray
        RMS of the signal.
    """
    sqData = data**2
    kernel = np.ones(kernelSize) / kernelSize
    rms = np.sqrt(signal.convolve(sqData, kernel, mode="valid"))
    return rms


def majorityVoting(labels: np.ndarray, windowSize: int) -> np.ndarray:
    """Apply majority voting on the labels predicted by a model.

    Parameters
    ----------
    labels : ndarray
        Labels to smooth with shape (nSamp,).
    windowSize : int
        Size of the window for majority voting.

    Returns
    -------
    ndarray
        Smoothed labels with shape (nSamp - windowSize,).
    """
    yMaj = np.zeros(labels.shape[0] - windowSize)
    for idx in range(labels.shape[0] - windowSize):
        yMaj[idx] = np.argmax(np.bincount(labels[idx : idx + windowSize]))
    return yMaj
