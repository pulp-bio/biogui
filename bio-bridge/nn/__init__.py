# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Neural network module for BioBridge middleware.

Provides the neural network architecture and training utilities
for ultrasound-based gesture recognition.

Components:
- us_encoder: Network architecture (US_Simple_Class, encoder blocks)
- train_utils: Training utilities (dataloaders, training loop, testing)
- seeds: Reproducibility seed configuration
"""

from .architectures.us_simple_cnn import US_Simple_Class

__all__ = [
    "US_Simple_Class",
]
