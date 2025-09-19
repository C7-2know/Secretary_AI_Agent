from datetime import datetime, timedelta
import pytz

def parse_business_window(base: datetime, tz: str = "America/New_York"):
    # Returns a default morning window for the given date
    zone = pytz.timezone(tz)
    start = zone.localize(datetime(base.year, base.month, base.day, 9, 0))
    end = zone.localize(datetime(base.year, base.month, base.day, 12, 0))
    return start, end

def pick_slots(freebusy: list, duration_min: int, limit: int = 3):
    # freebusy: list of (start_dt, end_dt) available intervals
    # returns list of candidate start times
    results = []
    dur = timedelta(minutes=duration_min)
    for (s, e) in freebusy:
        t = s
        while t + dur <= e and len(results) < limit:
            results.append(t)
            t += timedelta(minutes=15)
        if len(results) >= limit:
            break
    return results
