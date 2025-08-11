import numpy as np
import pandas as pd

import pricing_model

_MODEL = None


def _age_price_curve(age_years: float) -> float:
    """Return a price multiplier for a player's age.

    A bell-shaped curve is approximated by multiplying two sigmoids: one that
    raises values through the teenage years and another that decreases them for
    veterans.  The peak is normalised to ``1`` so the returned value can be used
    as a direct multiplier.
    """

    young = 1 / (1 + np.exp(-(age_years - 17) / 1.5))
    decline = 1 / (1 + np.exp((age_years - 30) / 2))
    factor = young * decline
    # Max value of the above product for ages 10-45 is ~0.953
    return float(factor / 0.9532287752233033)


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

    age_days = player.get("age_days")
    age_years = player.get("age_years")
    if age_years is None and age_days is not None:
        age_years = age_days / 365
    age_factor = _age_price_curve(age_years) if age_years is not None else 1.0

    price_pred *= age_factor
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
