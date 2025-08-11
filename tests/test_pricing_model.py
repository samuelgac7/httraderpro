import pricing
import pandas as pd


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


def test_age_extremes_reduce_price():
    base = {"playmaking": 6, "passing": 3, "defending": 3, "scoring": 3,
            "winger": 2, "form": 5, "tsi": 4000, "age_days": 9000,
            "specialty_index": 0}
    young = base.copy()
    old = base.copy()
    young["age_days"] = 4000  # very young
    old["age_days"] = 15000   # very veteran

    base_out = pricing.predict_price_from_comparables(base, None)
    young_out = pricing.predict_price_from_comparables(young, None)
    old_out = pricing.predict_price_from_comparables(old, None)

    assert young_out["price_pred"] < base_out["price_pred"]
    assert old_out["price_pred"] < base_out["price_pred"]


def test_no_single_attribute_dominates():
    player = {
        "playmaking": 10,
        "passing": 10,
        "defending": 10,
        "scoring": 10,
        "winger": 10,
        "form": 5,
        "tsi": 50_000,
        "age_days": 8_000,
        "specialty_index": 0,
    }
    comparable = player.copy()
    comparable["playmaking"] = 15
    comparable["tsi"] = 150_000
    comparable["age_days"] = 10_000

    contribs = pricing.attribute_contributions(player, comparable)
    total = sum(contribs.values())
    assert total > 0
    assert all(c <= total * 0.5 for c in contribs.values())


def test_goalkeeper_alternate_weights():
    comps = pd.DataFrame([
        {
            "price": 1_000_000,
            "playmaking": 0,
            "passing": 0,
            "defending": 0,
            "scoring": 0,
            "winger": 0,
            "form": 5,
            "tsi": 1000,
            "age_days": 5000,
            "specialty_index": 0,
            "goalkeeping": 8,
            "set_pieces": 5,
        },
        {
            "price": 2_000_000,
            "playmaking": 0,
            "passing": 0,
            "defending": 0,
            "scoring": 0,
            "winger": 0,
            "form": 5,
            "tsi": 1000,
            "age_days": 5000,
            "specialty_index": 0,
            "goalkeeping": 1,
            "set_pieces": 5,
        },
    ])

    gk_player = {
        "playmaking": 0,
        "passing": 0,
        "defending": 0,
        "scoring": 0,
        "winger": 0,
        "form": 5,
        "tsi": 1000,
        "age_days": 5000,
        "specialty_index": 0,
        "goalkeeping": 8,
        "set_pieces": 5,
    }

    field_player = gk_player.copy()
    field_player["goalkeeping"] = 1

    gk_price = pricing.predict_price_from_comparables(gk_player, comps, min_comps=1)
    field_price = pricing.predict_price_from_comparables(field_player, comps, min_comps=1)

    assert gk_price["price_pred"] < field_price["price_pred"]
    assert gk_price["price_pred"] < 1_500_000
