import pricing


def test_predict_positive():
    player = {"playmaking": 8, "passing": 5, "defending": 4, "scoring": 3,
              "winger": 2, "form": 7, "tsi": 5000, "age_days": 8000,
              "specialty_index": 1}
    out = pricing.predict_price_from_comparables(player, None)
    assert 0 < out["price_pred"] < 15_000_000
    assert out["p05"] <= out["price_pred"] <= out["p95"]
    assert out["p25"] <= out["price_pred"] <= out["p75"]


def test_playmaking_increases_price():
    base = {"playmaking": 6, "passing": 3, "defending": 3, "scoring": 3,
            "winger": 2, "form": 5, "tsi": 4000, "age_days": 9000,
            "specialty_index": 0}
    better = base.copy()
    better["playmaking"] = 11

    out_base = pricing.predict_price_from_comparables(base, None)
    out_better = pricing.predict_price_from_comparables(better, None)
    assert out_better["price_pred"] > out_base["price_pred"]
