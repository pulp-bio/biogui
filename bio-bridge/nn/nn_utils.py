"""
Docstring for nn.nn_utils
This file contains utils function to load Pre-Trained Neural Networks
"""

import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any



def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise TypeError(f"JSON at {path} is not a dict.")
    return obj

def get_model_name_and_kwargs(pre_meta: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Recover model factory name and model_kwargs from pretrained metadata (if present).
    """
    model_name = pre_meta.get("model_name", None)
    model_kwargs = pre_meta.get("model_kwargs", None) or {}
    if not isinstance(model_kwargs, dict):
        # if it was stored as string, try to decode
        try:
            model_kwargs = json.loads(model_kwargs)
        except Exception:
            model_kwargs = {}
    return model_name, model_kwargs