import numpy as np
import pandas as pd

def age_discount_factor(age_days:int):
    return max(0.75, 1.0 - 0.015 * (age_days/10.0))

def specialty_premium(spec_idx:int):
    table = {0:0.00, 1:0.03, 2:0.06, 3:0.04, 4:0.01, 5:0.02}
    return table.get(spec_idx, 0.0)

def predict_price_from_comparables(player, comp_df:pd.DataFrame|None):
    base_pred = 3_000_000
    if comp_df is None or comp_df.empty or "price" not in comp_df.columns:
        pm = player.get("playmaking",7)
        v = base_pred * (1 + 0.22*(pm - 7))
        v *= 1 + 0.05*(player.get("passing",0))
        v *= 1 + 0.03*(player.get("defending",0))
        v *= 1 + 0.02*(player.get("winger",0))
        v *= 1 + 0.03*(player.get("scoring",0))
        v *= 1 + 0.01*(player.get("form",0))
        v *= 1 + 0.0002*(player.get("tsi",0))
        v *= age_discount_factor(player.get("age_days",0))
        v *= (1 + specialty_premium(player.get("specialty_index",0)))
        return {"price_pred": v, "p25": v*0.7, "p75": v*1.3, "p05": v*0.5, "p95": v*1.6, "confidence": 0.4}

    df = comp_df.copy()
    for c in ["playmaking","age_days","passing","defending","scoring","winger","form","tsi","specialty_index"]:
        if c not in df.columns: df[c]=0

    def score_row(r):
        score = 0.0
        score += 2.0*abs(r["playmaking"] - player.get("playmaking",7))
        score += 0.1*abs(r["age_days"] - player.get("age_days",0))/10.0
        score += 0.5*abs(r["passing"] - player.get("passing",0))
        score += 0.5*abs(r["defending"] - player.get("defending",0))
        score += 0.4*abs(r["winger"] - player.get("winger",0))
        score += 0.4*abs(r["scoring"] - player.get("scoring",0))
        score += 0.2*abs(r["form"] - player.get("form",0))
        score += 0.0001*abs(r["tsi"] - player.get("tsi",0))
        score += 0.3*abs(r["specialty_index"] - player.get("specialty_index",0))
        return score
    df["score"] = df.apply(score_row, axis=1)
    df = df.sort_values("score").head(50)

    df["w"] = 1.0 / (1.0 + df["score"])
    price_pred = (df["price"]*df["w"]).sum() / (df["w"].sum() + 1e-9)

    price_pred *= age_discount_factor(player.get("age_days",0))
    price_pred *= (1 + specialty_premium(player.get("specialty_index",0)))

    p25 = float(np.percentile(df["price"], 25))
    p75 = float(np.percentile(df["price"], 75))
    p05 = float(np.percentile(df["price"], 5))
    p95 = float(np.percentile(df["price"], 95))
    spread = max(0.2, (p75 - p25) / max(1.0, price_pred))
    confidence = float(np.clip(1.0 - spread, 0.25, 0.9))
    return {"price_pred": float(price_pred), "p25": p25, "p75": p75, "p05": p05, "p95": p95, "confidence": confidence}
