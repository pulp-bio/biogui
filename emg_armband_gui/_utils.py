"""This module contains utility functions.


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

import json
import os

import numpy as np
import serial.tools.list_ports
from scipy import signal


def serialPorts():
    """Lists serial port names

    Returns
    -------
    list of str
        A list of the serial ports available on the system.
    """
    return [info[0] for info in serial.tools.list_ports.comports()]


def loadValidateJSON(file_path: str) -> dict | None:
    """Load and validate a JSON file representing the experiment configuration.

    Parameters
    ----------
    file_path : str
        Path the the JSON file.

    Returns
    -------
    dict or None
        Dictionary corresponding to the configuration, or None if it's not valid.
    """
    with open(file_path) as f:
        config = json.load(f)
    # Check keys
    provided_keys = set(config.keys())
    valid_keys = set(("gestures", "n_reps", "duration_ms", "image_folder"))
    if provided_keys != valid_keys:
        return None
    # Check paths
    if not os.path.isdir(config["image_folder"]):
        return None
    for image_path in config["gestures"].values():
        image_path = os.path.join(config["image_folder"], image_path)
        if not (
            os.path.isfile(image_path)
            and (image_path.endswith(".png") or image_path.endswith(".jpg"))
        ):
            return None

    return config


def loadValidateTrainData(filePath: str, nCh: int) -> np.ndarray | None:
    """Load and validate a .bin file containg 16 channels sEMG data and 1 label channel.

    Parameters
    ----------
    filePath : str
        Path the the .bin file.
    nCh : int
        Expected number of channels.

    Returns
    -------
    ndarray or None
        Training data with shape (nSamp, nCh + 1) or None if the file is not valid.
    """
    # Open file and check if it is reshapable
    with open(filePath, "rb") as f:
        data = np.fromfile(f, dtype="float32")
    if data.shape % (nCh + 1) != 0:
        return None

    return data.reshape(-1, nCh + 1)


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
    abs_diff = np.abs(np.diff(data))
    kernel = np.ones(kernelSize)
    wl = signal.convolve(abs_diff, kernel, mode="valid")
    return wl


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
