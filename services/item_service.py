"""
services/item_service.py

Orchestrates creating a lost/found report: persist the item, run AI
attribute extraction (with fallback), embed it, and index it in FAISS.

Returns a structured result instead of calling any `st.*` UI functions
directly, so `app.py` stays the only place that renders progress/toasts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai.embeddings import add_to_index, build_text_for_embedding, get_embedding
from database.queries import insert_item, insert_item_features
from services.image_service import save_image
from services.provider_service import ProviderManager


@dataclass
class CreateItemResult:
    item_id: int
    ai_features: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


def create_item(
    type_: str,
    title: str,
    desc: str,
    category: str,
    brand: str,
    color: str,
    location: str,
    date: str,
    time_: str,
    image_file: Optional[Any],
    user_id: Optional[int] = None,
) -> CreateItemResult:
    """Create a lost/found item end-to-end.

    Each stage (image save, AI extraction, embedding/indexing) is isolated
    so a failure in one doesn't take down the whole report: the item row is
    always created first, and any downstream problem is surfaced as a
    warning on the returned result rather than an exception.
    """
    warnings: List[str] = []

    img_path: Optional[str] = None
    if image_file:
        try:
            img_path = save_image(image_file, type_)
        except ValueError as exc:
            warnings.append(f"Image not saved: {exc}")

    item_id = insert_item(
        type_, title, desc, category, brand, color, location, date, time_, img_path, user_id=user_id
    )

    # --- AI attribute extraction (falls back internally; never raises) ---
    provider_manager = ProviderManager()
    text_for_ai = f"{title}. {desc}. Brand {brand}. Color {color}. Location {location}"
    features = provider_manager.analyze_with_fallback(text_for_ai)

    try:
        insert_item_features(
            item_id=item_id,
            ai_category=str(features.get("category")),
            ai_brand_json=json.dumps(features.get("brand")),
            ai_colors_json=json.dumps(features.get("primary_color")),
            ai_features_json=json.dumps(features.get("distinctive_features")),
            ai_confidence_json=json.dumps(features),
        )
    except Exception as exc:
        warnings.append(f"AI features could not be saved: {exc}")

    # --- Embedding + FAISS indexing ---
    try:
        emb_text = build_text_for_embedding(
            title, desc, brand, color, json.dumps(features.get("distinctive_features")), location
        )
        embedding = get_embedding(emb_text)
        add_to_index(item_id, embedding)
    except Exception as exc:
        warnings.append(f"Item saved, but search indexing failed: {exc}")

    return CreateItemResult(item_id=item_id, ai_features=features, warnings=warnings)
