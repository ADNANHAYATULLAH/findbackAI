"""
utils/time.py

Date/time parsing and a time-proximity similarity score used by the
matcher (items reported closer together in time are more likely matches).
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Optional


def parse_dt(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse a `YYYY-MM-DD` date + `HH:MM` time into a datetime.

    Falls back to date-only parsing if the time component is missing or
    malformed, and returns None (never raises) if both fail.
    """
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None


def time_similarity(d1: str, t1: str, d2: str, t2: str) -> float:
    """Exponential-decay similarity: ~1.0 within a few hours, ~0.7 at 24h,
    ~0.2 after about a week. Returns a neutral 0.5 if either time is
    unparseable so missing data doesn't unfairly tank a match score."""
    dt1 = parse_dt(d1, t1)
    dt2 = parse_dt(d2, t2)
    if not dt1 or not dt2:
        return 0.5
    hours = abs((dt2 - dt1).total_seconds()) / 3600
    return float(math.exp(-hours / 72))
