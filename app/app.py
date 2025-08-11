import os, sys
import numpy as np
import pandas as pd
from datetime import datetime
from dateutil import tz, relativedelta
import streamlit as st

# allow local imports when running from repo root
sys.path.append(os.path.dirname(__file__))

# Optional: pyCHPP
try:
    from pychpp import CHPP
    PCHPP_AVAILABLE = True
except Exception:
    PCHPP_AVAILABLE = False

from ui_helpers import themed_header, kpi_card, badge, parse_player_id_from_url, moneyfmt, df_download_button
from pricing import predict_price_from_comparables
from scheduler import recommend_expiry_slots, compute_publish_time
from features import extract_features_from_player
from ho_import import parse_ho_csv, parse_ho_paste, ho_specialty_to_index
from ics_utils import make_ics_single

st.set_page_config(page_title="HT Trader Pro", layout="wide")
themed_header("📈 HT Trader Pro", "CHPP + HO! • Market analytics, batch import, and auction timing")

with st.sidebar:
    st.markdown("### 🔐 CHPP Integration")
    st.caption("Official Hattrick API. No scraping.")
    chpp_status = badge("pyCHPP installed" if PCHPP_AVAILABLE else "pyCHPP not available", good=PCHPP_AVAILABLE)
    st.write(chpp_status, unsafe_allow_html=True)

    consumer_key = st.text_input("Consumer Key (CHPP)", value=os.getenv("HT_CHPP_KEY", ""))
    consumer_secret = st.text_input("Consumer Secret (CHPP)", value=os.getenv("HT_CHPP_SECRET", ""), type="password")

    if "chpp_tokens" not in st.session_state:
        st.session_state["chpp_tokens"] = None
    if "chpp_auth" not in st.session_state:
        st.session_state["chpp_auth"] = None

    chpp = None
    if PCHPP_AVAILABLE and consumer_key and consumer_secret:
        if st.session_state["chpp_tokens"]:
            chpp = CHPP(consumer_key, consumer_secret,
                        st.session_state["chpp_tokens"]["key"],
                        st.session_state["chpp_tokens"]["secret"])
            st.success("Connected to CHPP (tokens in session).")
        else:
            if st.button("1) Generate auth URL"):
                try:
                    chpp_tmp = CHPP(consumer_key, consumer_secret)
                    auth = chpp_tmp.get_auth(scope="")
                    st.session_state["chpp_auth"] = auth
                    st.session_state["chpp_tmp"] = {"key": consumer_key, "secret": consumer_secret}
                    st.info("Open the URL, authorize, then paste the CODE below.")
                    st.code(auth["url"])
                except Exception as e:
                    st.error(f"Error generating URL: {e}")

            code = st.text_input("2) Paste CODE from Hattrick")
            if st.session_state.get("chpp_auth") and code and st.button("3) Get tokens"):
                try:
                    chpp_tmp = CHPP(st.session_state["chpp_tmp"]["key"], st.session_state["chpp_tmp"]["secret"])
                    access_token = chpp_tmp.get_access_token(
                        request_token=st.session_state["chpp_auth"]["oauth_token"],
                        request_token_secret=st.session_state["chpp_auth"]["oauth_token_secret"],
                        code=code
                    )
                    st.session_state["chpp_tokens"] = {
                        "key": access_token["key"],
                        "secret": access_token["secret"]
                    }
                    st.success("Tokens stored in session.")
                except Exception as e:
                    st.error(f"Error retrieving tokens: {e}")

tab1, tab2, tab3, tab4 = st.tabs(["Link (CHPP)", "HO! CSV", "HO! paste", "Batch + Agenda"])

player_data = None

with tab1:
    st.caption("Paste player link. Requires CHPP to fetch automatically.")
    url = st.text_input("Player link", placeholder="https://www.hattrick.org/Club/Players/Player.aspx?playerId=123456789")
    from ui_helpers import parse_player_id_from_url
    player_id = parse_player_id_from_url(url) if url else None
    if player_id and chpp:
        try:
            player = chpp.player(int(player_id))
            player_data = extract_features_from_player(player)
            st.success(f"Loaded via CHPP: {player_data.get('name','(no name)')} (ID {player_id})")
        except Exception as e:
            st.error(f"CHPP error: {e}")

with tab2:
    st.caption("Export in HO!: CSV Player Export. Upload CSV and choose the player.")
    up = st.file_uploader("Upload HO! CSV", type=["csv"], key="ho_csv_single")
    if up is not None:
        try:
            ho_df = parse_ho_csv(up.read().decode("utf-8", errors="ignore"))
            if not ho_df.empty:
                opt = st.selectbox("Select player", options=list(ho_df["Name"]))
                row = ho_df[ho_df["Name"] == opt].iloc[0].to_dict()
                player_data = {
                    "id": None,
                    "name": row.get("Name","(Player)"),
                    "age_years": int(row.get("AgeYears",17)),
                    "age_days": int(row.get("AgeDays",0)),
                    "playmaking": int(row.get("Playmaking",0)),
                    "passing": int(row.get("Passing",0)),
                    "defending": int(row.get("Defending",0)),
                    "scoring": int(row.get("Scoring",0)),
                    "winger": int(row.get("Winger",0)),
                    "stamina": int(row.get("Stamina",0)),
                    "tsi": int(row.get("TSI",0)),
                    "form": int(row.get("Form",0)),
                    "experience": int(row.get("Experience",0)),
                    "specialty": row.get("Specialty","None"),
                    "specialty_index": ho_specialty_to_index(row.get("Specialty","None")),
                }
                st.success(f"Loaded from HO!: {player_data['name']}")
            else:
                st.warning("Could not detect standard columns. Check the file.")
        except Exception as e:
            st.error(f"CSV read error: {e}")

with tab3:
    st.caption("From HO!, copy/paste the player's table (text). The app will try to detect fields.")
    pasted = st.text_area("Paste text", height=180, placeholder="Name: ...\nAge: 17 years and 5 days\nPlaymaking: Solid (7)\n...")
    if pasted.strip():
        try:
            row = parse_ho_paste(pasted)
            if row:
                player_data = {
                    "id": None,
                    "name": row.get("Name","(Player)"),
                    "age_years": int(row.get("AgeYears",17)),
                    "age_days": int(row.get("AgeDays",0)),
                    "playmaking": int(row.get("Playmaking",0)),
                    "passing": int(row.get("Passing",0)),
                    "defending": int(row.get("Defending",0)),
                    "scoring": int(row.get("Scoring",0)),
                    "winger": int(row.get("Winger",0)),
                    "stamina": int(row.get("Stamina",0)),
                    "tsi": int(row.get("TSI",0)),
                    "form": int(row.get("Form",0)),
                    "experience": int(row.get("Experience",0)),
                    "specialty": row.get("Specialty","None"),
                    "specialty_index": ho_specialty_to_index(row.get("Specialty","None")),
                }
                st.success(f"Loaded from paste: {player_data['name']}")
            else:
                st.warning("No recognizable data in pasted text.")
        except Exception as e:
            st.error(f"Parse error: {e}")

with tab4:
    st.caption("Upload your HO! CSV to estimate **the whole squad** and generate an ICS for the Saturday peak expiry.")
    up_b = st.file_uploader("Upload HO! CSV (batch)", type=["csv"], key="ho_csv_batch")
    comp_b = st.file_uploader("Optional: comparables with prices (CSV)", type=["csv"], key="comps_batch")
    comps = None
    if comp_b is not None:
        try:
            comps = pd.read_csv(comp_b)
        except Exception:
            try:
                comps = pd.read_csv(comp_b, sep=";")
            except Exception:
                comps = None
    if up_b is not None:
        ho_df = parse_ho_csv(up_b.read().decode("utf-8", errors="ignore"))
        rows = []
        for _, r in ho_df.iterrows():
            p = {
                "name": r["Name"],
                "age_years": int(r["AgeYears"]),
                "age_days": int(r["AgeDays"]),
                "playmaking": int(r["Playmaking"]),
                "passing": int(r["Passing"]),
                "defending": int(r["Defending"]),
                "scoring": int(r["Scoring"]),
                "winger": int(r["Winger"]),
                "stamina": int(r["Stamina"]),
                "tsi": int(r["TSI"]),
                "form": int(r["Form"]),
                "experience": int(r["Experience"]),
                "specialty_index": ho_specialty_to_index(r.get("Specialty","None"))
            }
            pred = predict_price_from_comparables(p, comps)
            rows.append({
                "Name": p["name"],
                "AgeYears": p["age_years"],
                "AgeDays": p["age_days"],
                "Playmaking": p["playmaking"],
                "PriceExpected": round(pred["price_pred"]),
                "P25": round(pred["p25"]),
                "P75": round(pred["p75"]),
                "Confidence": round(pred["confidence"]*100)
            })
        out_df = pd.DataFrame(rows)
        st.dataframe(out_df, use_container_width=True, height=360)
        df_download_button(out_df, "predictions.csv", "⬇️ Download predictions CSV")

        tzname = "America/Santiago"
        sat_exp = recommend_expiry_slots(tzname, (15,45), (15,45))["sat_expiry"]
        publish_at = compute_publish_time(sat_exp)

        st.markdown(f"**Recommended expiry:** {sat_exp.strftime('%A %d-%m-%Y %H:%M %Z')}  •  **Publish:** {publish_at.strftime('%A %d-%m-%Y %H:%M %Z')}")

        ics_bytes = make_ics_single("Auction expiry (HT)", sat_exp, "Publish 72h before to hit peak", tzname)
        st.download_button("📅 Download ICS (Saturday expiry)", data=ics_bytes, file_name="saturday_expiry.ics", mime="text/calendar")

st.markdown("---")
st.markdown("### 🔎 Price prediction (single player)")
uploaded_comps = st.file_uploader("Upload comparables (CSV with prices)", type=["csv"], key="comps_single")
comp_df = None
if uploaded_comps is not None:
    try:
        comp_df = pd.read_csv(uploaded_comps)
    except Exception:
        try:
            comp_df = pd.read_csv(uploaded_comps, sep=";")
        except Exception as e:
            st.error(f"Could not read comparables CSV: {e}")

if player_data:
    pred = predict_price_from_comparables(player_data, comp_df)
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Expected price", moneyfmt(pred["price_pred"]))
    kpi_card(c2, "50% range (P25–P75)", f"{moneyfmt(pred['p25'])} – {moneyfmt(pred['p75'])}")
    kpi_card(c3, "90% range (P05–P95)", f"{moneyfmt(pred['p05'])} – {moneyfmt(pred['p95'])}")
    kpi_card(c4, "Confidence", f"{int(pred['confidence']*100)}%")

    st.markdown("### ⏱ Timing for peak (Saturday 15:45 Chile)")
    tzname = "America/Santiago"
    sat_exp = recommend_expiry_slots(tzname, (15,45), (15,45))["sat_expiry"]
    publish_at = compute_publish_time(sat_exp)
    c5, c6 = st.columns(2)
    kpi_card(c5, "Expires (Saturday)", sat_exp.strftime("%A %d-%m-%Y %H:%M %Z"))
    kpi_card(c6, "Publish at", publish_at.strftime("%A %d-%m-%Y %H:%M %Z"))
else:
    st.info("Load a player (CHPP or HO!) to see the prediction.")

st.caption("HO! for your data; CHPP for live comparables. No scraping.")
