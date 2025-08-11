import streamlit as st
import re
import pandas as pd

def themed_header(title, subtitle=""):
    st.markdown(f"<div style='display:flex;align-items:flex-end;gap:12px'><h1 style='margin-bottom:0'>{title}</h1><span style='opacity:0.7'>{subtitle}</span></div>", unsafe_allow_html=True)

def kpi_card(container, title, value):
    with container:
        st.markdown(
            f"""
        <div style="padding:12px;border:1px solid rgba(255,255,255,0.1);border-radius:16px">
        <div style="opacity:.7;font-size:.9rem">{title}</div>
        <div style="font-size:1.4rem;font-weight:700">{value}</div>
        </div>
        """,
            unsafe_allow_html=True
        )

def badge(text, good=True):
    color = "#10b981" if good else "#ef4444"
    return f"<span style='background:{color};color:white;padding:2px 8px;border-radius:999px;font-size:.8rem'>{text}</span>"

def parse_player_id_from_url(url:str):
    if not url: return None
    m = re.search(r'(?:playerId|PlayerID|playerid)=(\d+)', url)
    return int(m.group(1)) if m else None

def moneyfmt(x):
    try:
        return f"${int(round(float(x))):,}".replace(",", ".")
    except:
        return str(x)

def df_download_button(df:pd.DataFrame, filename:str, label:str="⬇️ Download CSV"):
    csv = df.to_csv(index=False)
    st.download_button(label, data=csv, file_name=filename, mime="text/csv")
