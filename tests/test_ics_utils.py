import ics_utils
from datetime import datetime
from dateutil import tz


def test_make_ics_single():
    tzinfo = tz.gettz("America/Santiago")
    expiry = datetime(2023, 1, 7, 15, 45, tzinfo=tzinfo)
    ics_bytes = ics_utils.make_ics_single("Training", expiry, "Session", "America/Santiago")

    start_fmt = ics_utils._fmt(expiry)
    expected = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//HT Trader Pro//EN
BEGIN:VEVENT
UID:{start_fmt}@httraderpro
DTSTAMP:{start_fmt}
DTSTART:{start_fmt}
DTEND:{start_fmt}
SUMMARY:Training
DESCRIPTION:Session
END:VEVENT
END:VCALENDAR
"""
    assert ics_bytes.decode("utf-8") == expected
