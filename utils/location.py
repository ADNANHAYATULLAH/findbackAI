"""
utils/location.py

Campus-location normalization and proximity scoring. Pure functions - no
I/O - so they're cheap to call per-candidate during matching.
"""

from __future__ import annotations

from typing import Dict, List

LOCATION_SYNONYMS: Dict[str, List[str]] = {
    "CS_DEPARTMENT": ["cs department", "computer science", "cs block", "cs building", "department of computer science"],
    "LIBRARY": ["library", "central library"],
    "CAFETERIA": ["cafeteria", "canteen", "cafe"],
    "MAIN_GATE": ["main gate", "entrance"],
    "HOSTEL": ["hostel", "dorm"],
    "PARKING": ["parking", "parking area"],
    "ADMIN_BLOCK": ["admin", "administration"],
    "LAB": ["laboratory", "lab", "computer lab"],
    "SPORTS": ["sports ground", "ground", "playground"],
}

NEARBY_MAP: Dict[str, List[str]] = {
    "CS_DEPARTMENT": ["LIBRARY", "LAB"],
    "LIBRARY": ["CS_DEPARTMENT", "CAFETERIA"],
}


def normalize_location(raw: str) -> str:
    """Map a free-text or dropdown location string to a canonical key."""
    if not raw:
        return "UNKNOWN"
    raw_lower = raw.lower()
    for norm, synonyms in LOCATION_SYNONYMS.items():
        if any(s in raw_lower for s in synonyms):
            return norm
    return raw.upper()[:30]


def location_similarity(l1: str, l2: str) -> float:
    """0..1 similarity between two normalized location keys.

    1.0 = identical, 0.7 = adjacent/nearby, 0.5 = unknown (neutral, doesn't
    penalize missing data), 0.1 = clearly different places.
    """
    if not l1 or not l2 or l1 == "UNKNOWN" or l2 == "UNKNOWN":
        return 0.5
    if l1 == l2:
        return 1.0
    if l2 in NEARBY_MAP.get(l1, []) or l1 in NEARBY_MAP.get(l2, []):
        return 0.7
    return 0.1
