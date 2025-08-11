from datetime import datetime
from dateutil import tz

def _fmt(dt:datetime):
    return dt.astimezone(tz.UTC).strftime("%Y%m%dT%H%M%SZ")

def make_ics_single(title:str, expiry_dt:datetime, description:str, tzname:str)->bytes:
    start = expiry_dt
    end = expiry_dt
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//HT Trader Pro//EN
BEGIN:VEVENT
UID:{_fmt(start)}@httraderpro
DTSTAMP:{_fmt(start)}
DTSTART:{_fmt(start)}
DTEND:{_fmt(end)}
SUMMARY:{title}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""
    return ics.encode("utf-8")
