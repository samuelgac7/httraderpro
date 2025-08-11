from datetime import datetime
from dateutil import tz, relativedelta

def next_weekday(target_weekday:int, now_dt, hour:int, minute:int):
    days_ahead = (target_weekday - now_dt.weekday()) % 7
    candidate = now_dt + relativedelta.relativedelta(days=days_ahead)
    candidate = candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now_dt:
        candidate += relativedelta.relativedelta(days=7)
    return candidate

def recommend_expiry_slots(tzname="America/Santiago", sat_hm=(15,45), wed_hm=(15,45)):
    tzinfo = tz.gettz(tzname)
    now = datetime.now(tz=tzinfo)
    sat_expiry = next_weekday(5, now, sat_hm[0], sat_hm[1])
    wed_expiry = next_weekday(2, now, wed_hm[0], wed_hm[1])
    return {"sat_expiry": sat_expiry, "wed_expiry": wed_expiry}

def compute_publish_time(expiry_dt, hours_before=72):
    return expiry_dt - relativedelta.relativedelta(hours=hours_before)
