import scheduler
from datetime import datetime
from dateutil import tz


def test_recommend_expiry_slots(monkeypatch):
    tzinfo = tz.gettz("America/Santiago")
    fixed_now = datetime(2023, 1, 2, 10, 0, tzinfo=tzinfo)  # Monday

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(scheduler, "datetime", FixedDatetime)
    slots = scheduler.recommend_expiry_slots()

    assert slots["sat_expiry"] == datetime(2023, 1, 7, 15, 45, tzinfo=tzinfo)
    assert slots["wed_expiry"] == datetime(2023, 1, 4, 15, 45, tzinfo=tzinfo)
