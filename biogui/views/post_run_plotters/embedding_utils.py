# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Shared PCA/t-SNE/UMAP embedding and label-coloring helpers for post-run feature analysis.
"""

from __future__ import annotations

import logging

import numpy as np
import pyqtgraph as pg

# Matplotlib "tab10" palette (RGB)
LABEL_PALETTE = [
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
]

# Labels always excluded from plots / embeddings (cannot be re-enabled from UI)
BASE_EXCLUDED_LABELS = {"init", "nan", ""}


def run_embedding(
    matrix: np.ndarray | None,
    labels: list[str],
    method: str,
) -> tuple[np.ndarray | None, list[str]]:
    """Project `matrix` to 2D via PCA/t-SNE/UMAP, returning coords and aligned labels."""
    try:
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        logging.warning("scikit-learn required (pip install scikit-learn).")
        return None, []

    if matrix is None:
        return None, []
    labels = list(labels)

    row_ok = np.isfinite(matrix).all(axis=1)
    matrix = matrix[row_ok]
    labels = [labels[i] for i, ok in enumerate(row_ok) if ok]

    if len(matrix) < 3:
        logging.warning("Not enough valid samples for embedding (need >= 3).")
        return None, []

    X = StandardScaler().fit_transform(matrix)

    if method == "PCA":
        from sklearn.decomposition import PCA

        X_2d = PCA(n_components=2).fit_transform(X)
    elif method == "t-SNE":
        from sklearn.manifold import TSNE

        perp = min(30, len(matrix) - 1)
        X_2d = TSNE(n_components=2, perplexity=perp, random_state=42).fit_transform(X)
    elif method == "UMAP":
        try:
            import umap as _umap

            nn = min(15, len(matrix) - 1)
            X_2d = _umap.UMAP(n_components=2, n_neighbors=nn, random_state=42).fit_transform(X)
        except ImportError:
            logging.warning("umap-learn not installed (pip install umap-learn).")
            return None, []
    else:
        return None, []

    return X_2d, labels


def refresh_embedding_plot(
    graphics_widget: pg.GraphicsLayoutWidget,
    X_2d: np.ndarray,
    labels: list[str],
    method: str,
    has_labels: bool,
) -> None:
    """Clear and redraw the embedding scatter plot, colored by label."""
    graphics_widget.clear()
    p: pg.PlotItem = graphics_widget.addPlot()
    p.setLabel("bottom", f"{method} dim 1")
    p.setLabel("left", f"{method} dim 2")
    title_suffix = "  —  coloured by label" if has_labels else ""
    p.setTitle(f"{method}{title_suffix}")
    p.showGrid(x=True, y=True, alpha=0.25)
    p.setAspectLocked(True)
    p.addLegend(labelTextSize="11pt")

    unique_labels = list(dict.fromkeys(labels))
    arr = np.array(labels)
    for i, lbl in enumerate(unique_labels):
        mask = arr == lbl
        r, g, b = LABEL_PALETTE[i % len(LABEL_PALETTE)]
        p.addItem(
            pg.ScatterPlotItem(
                x=X_2d[mask, 0],
                y=X_2d[mask, 1],
                size=8,
                pen=pg.mkPen(None),
                brush=pg.mkBrush(r, g, b, 180),
                name=lbl,
            )
        )
