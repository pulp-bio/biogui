# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Gesture prediction from ultrasound data.
"""

from pathlib import Path
import json
from typing import Any, Dict, Optional, Tuple
import numpy as np
import torch

from core import (
    US_WINDOW_SIZE,
    softmax,
)
from nn.architectures.models_factory import *

# from nn.architectures.us_simple_cnn import US_Simple_Class
from nn.nn_utils import get_model_name_and_kwargs


class GesturePredictor:
    """
    Handles model loading and inference for gesture/position recognition.

    Parameters
    ----------
    model_path : Path
        Path to the trained model checkpoint (.pth file)
    pre_meta:
        Metadata for the pre-trained Model

    num_transducers : int
        Number of ultrasound transducers/channels this model expects
    num_classes : int
        Number of output classes
    class_map : dict[int, str], optional
        Mapping from class indices to names
    device : str, optional
        Device to run inference on ('cpu' or 'cuda').
        Defaults to 'cpu'.

    Attributes
    ----------
    model : US_Simple_Class
        The loaded neural network model.
    device : torch.device
        Device used for inference.
    class_map : dict
        Mapping from class indices to names.
    """

    def __init__(
        self,
        model_path: Path,
        pre_meta: Dict,
        num_transducers: int,
        num_classes: int,
        class_map: dict[int, str],
        device: str = "cpu",
    ):

        model_name, model_kwargs = get_model_name_and_kwargs(pre_meta)
        # Register the MODEL
        model_name = pre_meta.get("model_name", None)
        print("Asked model name", model_name)
        self.model_factory = MODEL_REGISTRY[model_name]
        # print("Model factory is:", self.model_factory)
        # Extract Architecutre settings
        self.model_kwargs = model_kwargs
        print("Retrieved model args")
        print(self.model_kwargs)
        # Extract additional info needed
        ctx = dict(
            num_classes=num_classes,
            num_transducers=num_transducers,
            us_window_size=397,
        )
        if pre_meta.get("use_imu", False) is True:
            ctx["num_imu_columns"] = 3
        self.ctx = ctx
        # Extract transducers to use

        tx_used = pre_meta["transducers_used"]
        tx_to_int = []
        for tx in tx_used:
            tx_id_str = tx.replace("tx_", "")
            idx_to_consider = int(tx_id_str)
            # print(idx_to_consider)
            tx_to_int.append(idx_to_consider)
        self.us_idx_to_consider = tx_to_int

        self.model_path = Path(model_path)
        self.num_transducers = num_transducers
        print(
            f"Allocating model for #:{self.num_transducers} Transducers, Inferece will run on US idx:{self.us_idx_to_consider}"
        )
        self.num_classes = num_classes

        self.device = torch.device(device)
        self.class_map = class_map or {i: f"class_{i}" for i in range(num_classes)}

        # Load model
        self._load_model()

        # Pre-allocate tensor for efficiency (avoid allocation during inference)
        self.X_tensor = torch.empty(
            (1, num_transducers, US_WINDOW_SIZE),
            device=self.device,
        )

        print("\n\n")

    def _load_model(self):
        """Load model weights from checkpoint."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        # Load checkpoint
        checkpoint = torch.load(
            self.model_path,
            weights_only=False,
            map_location=self.device,
        )

        self.model = build_model(
            model_factory=self.model_factory, model_kwargs=self.model_kwargs, ctx=self.ctx
        )

        # Build the model depending on the Factory
        # self.model = US_Simple_Class(**self.ctx, **self.model_kwargs)

        # Initialize model architecture
        # self.model = US_Simple_Class(
        #    encoder_blocks_us=encoder_blocks_us,
        #    num_transducers=self.num_transducers,
        #    num_classes=self.num_classes,
        # )

        # Load weights
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

    def predict(
        self,
        us_data: np.ndarray,
        us_idx_to_consider: Optional[np.ndarray] = None,
        imu_data: Optional[np.ndarray] = None,
    ) -> tuple[int, str, np.ndarray]:
        """
        Predict class from ultrasound data and (Optionally) IMU data

        Parameters
        ----------
        us_data : np.ndarray
            Ultrasound data with shape (num_transducers, US_WINDOW_SIZE)

        Returns
        -------
        class_index : int
            Predicted class index
        class_name : str
            Human-readable class name from class_map
        probabilities : np.ndarray
            Softmax probabilities for each class

        Raises
        ------
        ValueError
            If us_data has incorrect shape
        """
        # Validate input shape
        expected_shape = (self.num_transducers, US_WINDOW_SIZE)
        if us_data.shape != expected_shape:
            raise ValueError(f"Expected us_data shape {expected_shape}, got {us_data.shape}")

        # Copy data into pre-allocated tensor
        if us_idx_to_consider is not None:
            self.X_tensor[0] = torch.from_numpy(us_data[us_idx_to_consider, :].astype(np.float32))
        else:
            # Copy all US data into pre-allocated tensor
            self.X_tensor[0] = torch.from_numpy(us_data.astype(np.float32))

        # Run inference
        with torch.no_grad():
            if imu_data is None:
                logits = self.model(self.X_tensor)
            else:
                imu_tensor = torch.from_numpy(imu_data.astype(np.float32)).unsqueeze(0)
                logits = self.model(self.X_tensor, imu_tensor)

            prediction = logits.argmax(dim=1).item()
            # Compute softmax probabilities
            probs = softmax(logits.cpu().numpy()[0])

        # Get class name
        class_name = self.class_map.get(prediction, f"Unknown({prediction})")

        return prediction, class_name, probs

    def get_confidence(self, probs: np.ndarray, class_idx: int) -> float:
        """
        Get confidence percentage for a prediction.

        Parameters
        ----------
        probs : np.ndarray
            Softmax probabilities
        class_idx : int
            Predicted class index

        Returns
        -------
        float
            Confidence as a percentage (0-100)
        """
        return probs[class_idx] * 100

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready for inference."""
        return self.model is not None

    def __repr__(self) -> str:
        return (
            f"GesturePredictor("
            f"model_path='{self.model_path}', "
            f"num_transducers={self.num_transducers}, "
            f"num_classes={self.num_classes}, "
            f"device='{self.device}'"
            f")"
        )
