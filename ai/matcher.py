"""
ai/matcher.py

Pure scoring functions that combine multiple similarity signals (text,
image, category, features, location, time, brand/color) into a single
weighted match score. No I/O, no Streamlit, no DB - fully unit-testable.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import numpy as np

MATCH_WEIGHTS: Dict[str, float] = {
    "text": 0.30,
    "image": 0.25,
    "category": 0.15,
    "features": 0.10,
    "location": 0.10,
    "time": 0.05,
    "brand_color": 0.05,
}


def cosine_sim(a: Optional[np.ndarray], b: Optional[np.ndarray]) -> float:
    """Cosine similarity between two (already-normalized) embeddings."""
    if a is None or b is None:
        return 0.0
    return float(np.dot(a, b))


def category_sim(c1: Optional[str], c2: Optional[str]) -> float:
    if not c1 or not c2:
        return 0.5
    return 1.0 if c1.lower() == c2.lower() else 0.2


def features_sim(f1: Optional[Iterable[str]], f2: Optional[Iterable[str]]) -> float:
    """Jaccard similarity between two sets of distinctive features."""
    if not f1 or not f2:
        return 0.5
    s1 = {x.lower() for x in f1}
    s2 = {x.lower() for x in f2}
    if not s1 or not s2:
        return 0.5
    union = s1 | s2
    return len(s1 & s2) / len(union) if union else 0.0


def brand_color_sim(
    b1: Optional[str], c1: Optional[str], b2: Optional[str], c2: Optional[str]
) -> float:
    score = 0.0
    if b1 and b2 and b1.lower() == b2.lower():
        score += 0.5
    if c1 and c2 and c1.lower() == c2.lower():
        score += 0.5
    if score > 0:
        return score
    return 0.3 if (b1 or c1) and (b2 or c2) else 0.5


def image_similarity_score(has_img1: bool, has_img2: bool, color_match: bool) -> float:
    """Placeholder visual-similarity heuristic until a real image-embedding
    comparison is wired in (both items need a photo to score above zero)."""
    if not has_img1 or not has_img2:
        return 0.0
    return 0.88 if color_match else 0.6


def final_score(scores: Dict[str, float]) -> float:
    """Weighted sum of component scores, expressed as a 0-100 percentage."""
    total = sum(scores[k] * MATCH_WEIGHTS[k] for k in MATCH_WEIGHTS)
    return round(total * 100, 1)


def label_for_score(score: float) -> str:
    if score >= 90:
        return "Very Strong Match"
    if score >= 75:
        return "Strong Match"
    if score >= 60:
        return "Possible Match"
    if score >= 40:
        return "Weak Match"
    return "Unlikely Match"
