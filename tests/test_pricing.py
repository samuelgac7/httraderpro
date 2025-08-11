import pandas as pd
from pricing import predict_price_from_comparables

def test_predict_with_comps():
    player = {"playmaking":7,"age_days":5,"passing":5,"defending":4,"scoring":3,"winger":4,"form":6,"tsi":1200,"specialty_index":2}
    comps = pd.DataFrame({
        "price":[5_000_000, 6_000_000, 4_500_000],
        "playmaking":[7,7,7],
        "age_days":[5,10,0],
        "passing":[5,5,4],
        "defending":[4,4,4],
        "scoring":[3,3,2],
        "winger":[4,4,3],
        "form":[6,6,5],
        "tsi":[1200,1100,1300],
        "specialty_index":[2,2,2],
    })
    out = predict_price_from_comparables(player, comps)
    assert out["price_pred"] > 0
    assert out["p25"] <= out["p75"]
    assert 0.25 <= out["confidence"] <= 0.95
