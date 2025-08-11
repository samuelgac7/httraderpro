import numpy as np
import pandas as pd

import pricing_model

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = pricing_model.load_model()
    return _MODEL


def predict_price_from_comparables(player, comp_df: pd.DataFrame | None):
    """Predict price using the trained model.

    The previous comparable-based logic has been replaced by a machine
    learning model. Any provided comparables are ignored.
    """
    model = _get_model()
    price_pred = pricing_model.predict(player, model)

    p25 = price_pred * 0.8
    p75 = price_pred * 1.2
    p05 = price_pred * 0.6
    p95 = price_pred * 1.4
    confidence = 0.5

    return {
        "price_pred": float(price_pred),
        "p25": float(p25),
        "p75": float(p75),
        "p05": float(p05),
        "p95": float(p95),
        "confidence": confidence,
    }
