"""
ai/schemas.py

Pydantic models for LLM attribute-extraction output, plus a resilient
`safe_parse_extraction` wrapper so a malformed or partial LLM response
never crashes the item-creation flow - it just degrades to defaults.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError


class BrandInfo(BaseModel):
    value: Optional[str] = None
    confidence: float = 0.0
    source: str = "unknown"


class ColorInfo(BaseModel):
    value: Optional[str] = None
    confidence: float = 0.0
    source: str = "unknown"


class ExtractedFeatures(BaseModel):
    category: Optional[str] = None
    brand: BrandInfo = Field(default_factory=BrandInfo)
    primary_color: ColorInfo = Field(default_factory=ColorInfo)
    secondary_colors: List[str] = Field(default_factory=list)
    object_type: Optional[str] = None
    distinctive_features: List[str] = Field(default_factory=list)
    visible_text: List[str] = Field(default_factory=list)
    condition: Optional[str] = "unknown"
    approximate_size: Optional[str] = "unknown"


def safe_parse_extraction(raw: Any) -> ExtractedFeatures:
    """Coerce whatever the LLM (or rule-based fallback) returned into a
    valid `ExtractedFeatures`, tolerating dirty/partial/wrong-typed input.

    - `raw` that isn't a dict -> defaults.
    - Fields with the wrong shape (e.g. brand as a bare string instead of
      {"value": ..., "confidence": ...}) are coerced into the expected shape.
    - Any remaining validation error -> defaults, never an exception.
    """
    if not isinstance(raw, dict):
        return ExtractedFeatures()

    data: Dict[str, Any] = dict(raw)

    # Tolerate providers/fallbacks that return brand/color as a bare string.
    for key in ("brand", "primary_color"):
        val = data.get(key)
        if isinstance(val, str):
            data[key] = {"value": val, "confidence": 0.5, "source": "text"}

    try:
        return ExtractedFeatures(**data)
    except ValidationError:
        # Retry with only the top-level keys pydantic recognizes as scalars;
        # anything still broken falls back to full defaults.
        safe_subset = {
            k: v for k, v in data.items() if k in ExtractedFeatures.model_fields
        }
        try:
            return ExtractedFeatures(**safe_subset)
        except ValidationError:
            return ExtractedFeatures()
