# Definitions of seeds for Data Preparation Loaders and Training script
# Following the guidelines at: https://docs.pytorch.org/docs/2.5/notes/randomness.html
import random

import numpy as np
import torch

PD_SAMPLE_SEED = 42

# Set RNG for all devices
torch.manual_seed(42)

# Set python seed as well for custom operations
random.seed(0)

# Set numpy seed
np.random.seed(0)

# Only enable deterministic algorithms on CPU
# On CUDA >= 10.2, this requires CUBLAS_WORKSPACE_CONFIG environment variable
# which is cumbersome to set up, so we disable it for CUDA
if not torch.cuda.is_available():
    torch.use_deterministic_algorithms(True)
