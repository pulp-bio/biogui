"""
models_factory.py

Centralized model factory and registry for experiments

This module provides:
- A registry of available model factories (MODEL_REGISTRY)
- A unified `build_model` function that instantiates a model given:
    - a factory function
    - optional model-specific keyword arguments
    - a context dictionary produced by the training pipeline

The goal is to decouple *model construction* from *training logic*, enabling:
- clean ablations
- easy architecture swaps
- reproducible experiments
"""
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]   
sys.path.insert(0, str(PROJECT_ROOT))

from typing import Callable, Dict, Any, Optional
import torch.nn as nn


################# POSSIBLE NETWORK ARCHITECTURES ######################
from nn.architectures.us_simple_cnn import *
from nn.architectures.us_imu_simple_cnn import * 

################# POSSIBLE NETWORK ARCHITECTURES ######################
# from training.config import * 
# from training.config.defines import IMU_COLUMNS


# -------------------------------------------------------------------------------------------------
# Model factory registry
# -------------------------------------------------------------------------------------------------

#: Maps model name (str) -> factory function
MODEL_REGISTRY: Dict[str, Callable[..., nn.Module]] = {}


def register_model(name: str):
    """
    Decorator to register a model factory under a given name.

    Example
    -------
    @register_model("simple_cnn")
    def simple_factory(...):
        return MyModel(...)

    Then:
        factory = MODEL_REGISTRY["simple_cnn"]
    """
    def deco(fn: Callable[..., nn.Module]):
        if name in MODEL_REGISTRY:
            raise ValueError(f"Model '{name}' already registered.")
        MODEL_REGISTRY[name] = fn
        return fn
    return deco


# -------------------------------------------------------------------------------------------------
# Model builder (used by training code)
# -------------------------------------------------------------------------------------------------

def build_model(
    model_factory: Optional[Callable[..., nn.Module]],
    model_kwargs: Optional[Dict[str, Any]],
    ctx: Dict[str, Any],
    ) -> nn.Module:
    """
    Build and return a model instance.

    Parameters
    ----------
    model_factory:
        A callable that builds and returns an nn.Module.
        If None, a default US_Simple_Class factory is used.
    model_kwargs:
        Optional dictionary of model-specific keyword arguments
        (e.g. dropout, width, depth, d_model, etc.).
    ctx:
        Context dictionary prepared by the training pipeline.
        Common keys include:
            - num_classes (int)
            - num_transducers (int)
            - us_window_size (int)
            - use_imu_data (bool)
            - imu_dim (int or None)

        Factories may ignore keys they do not need.

    Returns
    -------
    nn.Module
        Instantiated model.
    """

    # ---- Default factory fallback ---------------------------------------------------------------
    if model_factory is None:
        print("Back to default model")
        def default_factory(**ctx):
            return US_Simple_Class(
                num_transducers=ctx["num_transducers"],
                num_classes=ctx["num_classes"],
            )
        factory = default_factory
    else:
        factory = model_factory

    # ---- Safety checks --------------------------------------------------------------------------
    if not callable(factory):
        raise TypeError("model_factory must be callable or None.")

    model_kwargs = model_kwargs or {}

    # ---- Instantiate model ----------------------------------------------------------------------
    model = factory(**ctx, **model_kwargs)

    if not isinstance(model, nn.Module):
        raise TypeError(
            f"Model factory '{factory.__name__}' did not return an nn.Module."
        )
    #print("Built model:", type(model).__name__)
    #print("Model kwargs:", model_kwargs)

    return model


# -------------------------------------------------------------------------------------------------
# Registered model factories
# -------------------------------------------------------------------------------------------------

@register_model("simple_us_cnn")
def simple_factory(
    num_classes: int,
    num_transducers: int,
    us_window_size: int,
    filters=(1, 1),
    kernels=((3, 1), (3, 1)),
    max_pools=((4, 1), (4, 1)),
    dropout_rate: float = 0.05,
    head_hidden_mult: float = 0.5,
    **_,  # swallow tx_columns/use_imu_data/imu_dim safely
    ) -> nn.Module:
    return US_Simple_Class(
        num_transducers=num_transducers,
        num_classes=num_classes,
        us_window_size=us_window_size,
        filters=filters,
        kernels=kernels,
        max_pools=max_pools,
        dropout_rate=dropout_rate,
        head_hidden_mult=head_hidden_mult,
    )

@register_model("simple_us_imu_cnn")
def simple_fusion_factory(
    num_classes: int,
    num_transducers: int,
    us_window_size: int,
    num_imu_columns : int,                  # This is 3 by default 
    filters=(1, 1),
    kernels=((3, 1), (3, 1)),
    max_pools=((4, 1), (4, 1)),
    dropout_rate: float = 0.05,
    head_hidden_mult: float = 0.5,
    **_,  
    ) -> nn.Module:

    return US_IMU_Simple_Class(
        num_transducers=num_transducers,
        num_classes=num_classes,
        us_window_size=us_window_size,
        num_imu_channels = num_imu_columns, 
        filters=filters,
        kernels=kernels,
        max_pools=max_pools,
        dropout_rate=dropout_rate,
        head_hidden_mult=head_hidden_mult,
    )


# Example for future extension:
#
# @register_model("transformer")
# def transformer_factory(
#     num_classes: int,
#     num_transducers: int,
#     us_window_size: int,
#     d_model: int = 128,
#     n_layers: int = 4,
#     **_,
# ) -> nn.Module:
#     return USTransformer(
#         in_channels=num_transducers,
#         seq_len=us_window_size,
#         d_model=d_model,
#         n_layers=n_layers,
#         num_classes=num_classes,
#     )
