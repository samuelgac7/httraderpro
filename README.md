# HT Trader Pro

Read-only, compliance-first analytics for **Hattrick**:
- Import from **HO! CSV** or via **CHPP** (official API).
- Predict fair prices from comparables; show confidence bands.
- Plan auction expiry for **Saturday 15:45 America/Santiago** (peak).

## Run locally
```bash
pip install -r requirements.txt
python -m streamlit run app/app.py
```

## Env vars
Create a `.env` or set env vars:
```
HT_CHPP_KEY=your_chpp_consumer_key
HT_CHPP_SECRET=your_chpp_consumer_secret
```

> CHPP is optional for HO! CSV workflows. For live comparables you must have a CHPP product approved.

## Legal
This project **does not scrape** Hattrick. It uses CHPP (with user consent) and user-imported files (HO! CSV). See [PRIVACY](PRIVACY.md) and [TERMS](TERMS.md).
