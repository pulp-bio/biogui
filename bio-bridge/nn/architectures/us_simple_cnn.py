# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

import torch
import torch.nn as nn

from typing import Sequence, Tuple, List
import numpy as np


class US_CNN_BLOCK(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Tuple[int, int],
        max_pool_size: Tuple[int, int],
        dropout_rate: float = 0.05,
    ):
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                padding="same",
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.MaxPool2d(kernel_size=max_pool_size, stride=max_pool_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


def build_us_encoder(
    *,
    in_channels: int,
    filters: Sequence[int],
    kernels: Sequence[Tuple[int, int]],
    max_pools: Sequence[Tuple[int, int]],
    dropout_rate: float,
) -> nn.Sequential:
    """
    Create an encoder with one US_CNN_BLOCK per entry in filters/kernels/max_pools.
    Length of all lists must match.
    """
    n = len(filters)
    assert n > 0, "filters must contain at least one block."
    assert (
        len(kernels) == n and len(max_pools) == n
    ), "filters/kernels/max_pools must have same length"

    blocks: List[nn.Module] = []
    c_in = int(in_channels)

    for i in range(n):
        c_out = int(filters[i])
        blocks.append(
            US_CNN_BLOCK(
                in_channels=c_in,
                out_channels=c_out,
                kernel_size=tuple(kernels[i]),
                max_pool_size=tuple(max_pools[i]),
                dropout_rate=float(dropout_rate),
            )
        )
        c_in = c_out

    return nn.Sequential(*blocks)


def pooled_hw(
    us_window_size: int,
    num_transducers: int,
    max_pools: Sequence[Tuple[int, int]],
) -> Tuple[int, int]:
    """
    Compute (T_out, W_out) after applying MaxPool2d with kernel sizes max_pools.

    With x reshaped to (B, 1, T, C):
      - pooling p_h reduces T
      - pooling p_w reduces C
    """
    t = int(us_window_size)
    w = int(num_transducers)
    for p_h, p_w in max_pools:
        t //= int(p_h)
        w //= int(p_w)
    return t, w


class US_Simple_Class(nn.Module):
    """
    Parameterizable CNN classifier for ultrasound data.

    Input:  x shape (B, C=num_transducers, T=us_window_size)
    Intern: reshaped to (B, 1, T, C)
    """

    def __init__(
        self,
        *,
        num_transducers: int,
        num_classes: int,
        us_window_size: int = 397,
        filters: Sequence[int] = (1, 1),
        kernels: Sequence[Tuple[int, int]] = ((3, 1), (3, 1)),
        max_pools: Sequence[Tuple[int, int]] = ((4, 1), (4, 1)),
        dropout_rate: float = 0.05,
        head_hidden_mult: float = 0.5,  # hidden_dim = head_hidden_mult * feat_dim
    ):

        super().__init__()
        self.num_transducers = int(num_transducers)
        self.num_classes = int(num_classes)
        self.us_window_size = int(us_window_size)
        # print("Building US Simple Class with filters:", filters, "kernels:", kernels, "max_pools:", max_pools)
        assert len(filters) > 0, "filters must contain at least one block."

        # ---- Encoder ----
        self.encoder = build_us_encoder(
            in_channels=1,
            filters=filters,
            kernels=kernels,
            max_pools=max_pools,
            dropout_rate=dropout_rate,
        )

        # ---- Feature dimension after encoder ----
        T_out, W_out = pooled_hw(self.us_window_size, self.num_transducers, max_pools)
        assert T_out >= 1 and W_out >= 1, "Pooling too aggressive: collapsed dimension (<1)."

        C_out = int(filters[-1])  # output channels of last conv block
        feat_dim = T_out * W_out * C_out

        hidden_dim = max(1, int(feat_dim * float(head_hidden_mult)))
        mid_dim = max(1, hidden_dim // 2)

        # ---- Classification head ----
        self.head = nn.Sequential(
            nn.Linear(feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, mid_dim),
            nn.ReLU(),
            nn.Linear(mid_dim, self.num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, C, T) -> (B, 1, T, C)
        x = x[:, None].swapaxes(-1, -2)
        x = self.encoder(x)
        x = x.flatten(start_dim=1)
        return self.head(x)


# if __name__ == "__main__":
#     from torchsummary import summary

#     # ---- Old behavior settings ----
#     num_transducers = 6      # e.g. tx_forearm + tx_bicep
#     num_classes = 7
#     us_window_size = 397

#     kwargs = dict(
#         us_window_size=397,
#         filters=(3, 3, 3),
#         kernels=((3, 1), (3, 1), (3 ,1)),
#         max_pools=((4, 1), (4, 1), (4, 1)),
#         dropout_rate=0.05,
#         head_hidden_mult=0.5,
#     )

#     # ---- Build model ----
#     model = US_Simple_Class(
#         num_transducers=num_transducers,
#         num_classes=num_classes,
#         **kwargs,
#     )

#     # ---- Move to CPU (torchsummary requires explicit device) ----
#     device = torch.device("cpu")
#     model.to(device)

#     # ---- Print model summary ----
#     summary(
#         model,
#         input_size=(num_transducers, us_window_size),
#         device="cpu",
#     )
#     model_parameters = filter(lambda p: p.requires_grad, model.parameters())
#     params = sum([np.prod(p.size()) for p in model_parameters])
#     print("Model Number of Parameters:", params)
