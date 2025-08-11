import json
import os

import numpy as np
import pandas as pd

import pricing_model

_MODEL = None
_GK_MODEL = None


# Scaling factors for each attribute used when comparing two players.
# The values roughly correspond to either an expected range or a
# standard deviation so that differences are normalised before
# weighting.  They can be overridden via environment variables or
# function arguments.
DEFAULT_SCALES = {
    "playmaking": 5,
    "passing": 5,
    "defending": 5,
    "scoring": 5,
    "winger": 5,
    "form": 5,
    "tsi": 100_000,
    "age_days": 1_825,  # ~5 years
    "specialty_index": 1,
    "goalkeeping": 5,
    "set_pieces": 5,
}

DEFAULT_WEIGHTS = {k: 1.0 for k in DEFAULT_SCALES.keys()}

GOALKEEPER_WEIGHTS = {**DEFAULT_WEIGHTS, "goalkeeping": 3.0, "scoring": 0.5, "winger": 0.5, "playmaking": 0.5, "passing": 0.5}
GOALKEEPER_SCALES = {**DEFAULT_SCALES}


def _load_config(env_var: str) -> dict[str, float]:
    """Load a JSON encoded mapping from an environment variable."""

    data = os.getenv(env_var)
    if not data:
        return {}
    try:
        loaded = json.loads(data)
        return {k: float(v) for k, v in loaded.items()}
    except Exception:
        return {}


def attribute_contributions(
    player: dict,
    comparable: dict,
    weights: dict[str, float] | None = None,
    scales: dict[str, float] | None = None,
) -> dict[str, float]:
    """Return per-attribute contributions to the comparable score."""

    weights = weights or {
        **DEFAULT_WEIGHTS,
        **_load_config("PRICING_WEIGHTS"),
    }
    scales = scales or {
        **DEFAULT_SCALES,
        **_load_config("PRICING_SCALES"),
    }

    contribs: dict[str, float] = {}
    for attr, weight in weights.items():
        scale = scales.get(attr, 1.0)
        diff = (player.get(attr, 0) - comparable.get(attr, 0)) / scale
        contribs[attr] = abs(diff) * weight
    return contribs


def _distance(
    player: dict,
    comparable: dict,
    weights: dict[str, float] | None = None,
    scales: dict[str, float] | None = None,
) -> float:
    """Weighted distance between player and comparable."""

    contribs = attribute_contributions(player, comparable, weights, scales)
    return float(sum(contribs.values()))


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


def _get_gk_model():
    global _GK_MODEL
    if _GK_MODEL is None:
        _GK_MODEL = pricing_model.load_model_gk()
    return _GK_MODEL


def _filter_comparables(
    player: dict,
    comp_df: pd.DataFrame,
    *,
    age_range: float = 1.0,
    skill_delta: int = 1,
) -> pd.DataFrame:
    """Filter comparables by price outliers, age and skill levels.

    Prices outside 1.5 times the interquartile range are discarded. Only
    players within ``age_range`` years of the target player's age and whose
    core skills differ by at most ``skill_delta`` levels are kept.
    """

    df = comp_df.copy()

    if not df.empty and "price" in df.columns:
        q1 = df["price"].quantile(0.25)
        q3 = df["price"].quantile(0.75)
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        df = df[(df["price"] >= low) & (df["price"] <= high)]

    player_age = player.get("age_years")
    if player_age is None and (age_days := player.get("age_days")) is not None:
        player_age = age_days / 365
    if player_age is not None:
        if "age_years" in df.columns:
            comp_age = df["age_years"]
        elif "age_days" in df.columns:
            comp_age = df["age_days"] / 365
        else:
            comp_age = None
        if comp_age is not None:
            df = df[(comp_age >= player_age - age_range) & (comp_age <= player_age + age_range)]

    skill_cols = [
        "playmaking",
        "passing",
        "defending",
        "scoring",
        "winger",
        "goalkeeping",
    ]
    for col in skill_cols:
        p_val = player.get(col)
        if p_val is not None and col in df.columns:
            df = df[(df[col] >= p_val - skill_delta) & (df[col] <= p_val + skill_delta)]

    return df


def predict_price_from_comparables(
    player,
    comp_df: pd.DataFrame | None,
    *,
    min_comps: int = 3,
    weights: dict[str, float] | None = None,
    scales: dict[str, float] | None = None,
):
    """Predict price using either comparables or the trained model.

    If a DataFrame of comparables is provided, their prices are weighted by
    the inverse of the scaled, weighted distance to the target player.  The
    comparable DataFrame is first filtered for outlier prices and players with
    similar age and skill levels.  A minimum of ``min_comps`` valid comparables
    is required; otherwise the machine learning model is used.  The weighting
    parameters can be overridden via the ``weights`` and ``scales`` arguments or
    by setting the ``PRICING_WEIGHTS`` and ``PRICING_SCALES`` environment
    variables with JSON mappings.
    """

    is_gk = player.get("goalkeeping", 0) >= 7

    if comp_df is not None and not comp_df.empty:
        comp_df = _filter_comparables(player, comp_df)
        if len(comp_df) >= min_comps:
            default_w = GOALKEEPER_WEIGHTS if is_gk else DEFAULT_WEIGHTS
            default_s = GOALKEEPER_SCALES if is_gk else DEFAULT_SCALES
            weights = weights or {
                **default_w,
                **_load_config("PRICING_WEIGHTS"),
            }
            scales = scales or {
                **default_s,
                **_load_config("PRICING_SCALES"),
            }

            df = comp_df.copy()
            df["distance"] = df.apply(lambda r: _distance(player, r, weights, scales), axis=1)
            df["w"] = 1 / (1 + df["distance"])

            price_pred = float(np.average(df["price"], weights=df["w"]))
            p25 = float(np.percentile(df["price"], 25))
            p75 = float(np.percentile(df["price"], 75))
            p05 = float(np.percentile(df["price"], 5))
            p95 = float(np.percentile(df["price"], 95))
            confidence = float(df["w"].sum() / (df["w"].sum() + len(df)))
            return {
                "price_pred": price_pred,
                "p25": p25,
                "p75": p75,
                "p05": p05,
                "p95": p95,
                "confidence": confidence,
            }

    # Fall back to machine learning model when no comparables are provided.
    model = _get_gk_model() if is_gk else _get_model()
    price_pred = pricing_model.predict_gk(player, model) if is_gk else pricing_model.predict(player, model)

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
