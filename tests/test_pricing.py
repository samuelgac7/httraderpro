import pandas as pd
import pricing


def test_predict_price_no_comparables():
    player = {
        "playmaking": 6,
        "passing": 3,
        "defending": 3,
        "scoring": 3,
        "winger": 2,
        "form": 5,
        "tsi": 4000,
        "age_days": 9000,
        "specialty_index": 0,
    }
    result_none = pricing.predict_price_from_comparables(player, None)
    result_empty = pricing.predict_price_from_comparables(player, pd.DataFrame())
    assert result_none == result_empty


def test_predict_price_with_extreme_comparables_fallback():
    player = {
        "playmaking": 6,
        "passing": 3,
        "defending": 3,
        "scoring": 3,
        "winger": 2,
        "form": 5,
        "tsi": 4000,
        "age_days": 9000,
        "specialty_index": 0,
    }
    comps = pd.DataFrame([
        {**player, "price": 100_000},
        {**player, "price": 110_000},
        {**player, "price": 10_000_000, "age_days": 60 * 365, "playmaking": 20},
    ])
    result_none = pricing.predict_price_from_comparables(player, None)
    result_extreme = pricing.predict_price_from_comparables(player, comps)
    assert result_extreme == result_none
