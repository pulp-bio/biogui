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


def serial_ports():
    """Lists serial port names

    Returns
    -------
    list of str
        A list of the serial ports available on the system.
    """
    return [info[0] for info in serial.tools.list_ports.comports()]


def load_validate_json(file_path: str) -> dict | None:
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


def load_validate_train_data(file_path: str) -> np.ndarray | None:
    """Load and validate a .bin file containg 16 channels sEMG data and 1 label channel.

    Parameters
    ----------
    file_path : str
        Path the the .bin file.

    Returns
    -------
    np.ndarray or None
        numpy array (n_samples x (n_channels + label))
    """
    #open file and chek if it is reshapable
    with open(file_path, "rb") as f:
        try:
            data = np.fromfile(f, dtype="float32").reshape(-1,17)
        except ValueError:
            return None
    return data