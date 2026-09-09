"""
services/matching_service.py

Finds and scores candidate found-items for a given lost-item report:
FAISS semantic retrieval narrows the candidate pool, then each candidate
is scored across text/image/category/features/location/time/brand-color
signals and combined into a final weighted percentage.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import numpy as np

from ai.embeddings import build_text_for_embedding, get_embedding, load_faiss
from ai.matcher import (
    brand_color_sim,
    category_sim,
    features_sim,
    final_score,
    image_similarity_score,
    label_for_score,
)
from database.queries import get_item, get_item_features, get_items_by_type
from database.database import get_connection
from utils.location import location_similarity, normalize_location
from utils.time import time_similarity


def _lost_query_text(lost: Dict[str, Any]) -> str:
    return build_text_for_embedding(
        lost["title"], lost["description"], lost["brand"], lost["primary_color"], "", lost["location"]
    )


def _found_query_text(found: Dict[str, Any]) -> str:
    return build_text_for_embedding(
        found["title"], found["description"], found["brand"], found["primary_color"], "", found["location"]
    )


def _faiss_candidates(lost: Dict[str, Any], top_k: int) -> Dict[int, float]:
    """Return {found_item_id: cosine_text_score} using FAISS semantic search.

    Because embeddings are normalized and the index metric is inner
    product, the raw FAISS distance IS the cosine similarity - no need to
    recompute it per candidate.
    """
    index, meta = load_faiss()
    if index.ntotal == 0:
        return {}
    q_emb = get_embedding(_lost_query_text(lost))
    scores, indices = index.search(np.array([q_emb]).astype("float32"), min(top_k * 3, index.ntotal))
    out: Dict[int, float] = {}
    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(meta):
            out[int(meta[idx])] = float(score)
    return out


def find_matches_for_lost(lost_id: int, top_k: int = 10) -> List[Dict[str, Any]]:
    """Return the top-`top_k` scored found-item matches for a lost report."""
    lost = get_item(lost_id)
    if not lost:
        return []
    lost_feat = get_item_features(lost_id)

    faiss_scores = _faiss_candidates(lost, top_k)

    with get_connection() as conn:
        if faiss_scores:
            placeholders = ",".join("?" * len(faiss_scores))
            rows = conn.execute(
                f"SELECT * FROM items WHERE id IN ({placeholders}) AND type='found' AND status='active'",
                list(faiss_scores.keys()),
            ).fetchall()
            candidates = [dict(r) for r in rows]
        else:
            candidates = get_items_by_type("found", status="active")[:20]

        results: List[Dict[str, Any]] = []
        for found in candidates:
            found_feat_row = conn.execute(
                "SELECT * FROM item_features WHERE item_id=?", (found["id"],)
            ).fetchone()
            found_feat = dict(found_feat_row) if found_feat_row else None

            # Text similarity: reuse the FAISS score when available (cheap,
            # already computed), otherwise embed on the fly.
            if found["id"] in faiss_scores:
                text_score = max(0.0, min(1.0, faiss_scores[found["id"]]))
            else:
                text_score = max(
                    0.0,
                    min(
                        1.0,
                        float(np.dot(get_embedding(_lost_query_text(lost)), get_embedding(_found_query_text(found)))),
                    ),
                )

            if found_feat and lost_feat:
                try:
                    lost_features = json.loads(lost_feat["ai_features"])
                    found_features = json.loads(found_feat["ai_features"])
                    feat_score = features_sim(lost_features, found_features)
                except (json.JSONDecodeError, TypeError):
                    feat_score = 0.5
            else:
                feat_score = 0.5

            loc_score = location_similarity(
                normalize_location(lost["location"]), normalize_location(found["location"])
            )
            time_score = time_similarity(
                lost["event_date"], lost["event_time"], found["event_date"], found["event_time"]
            )
            cat_score = category_sim(lost["category"], found["category"])
            brand_color_score = brand_color_sim(
                lost["brand"], lost["primary_color"], found["brand"], found["primary_color"]
            )
            img_score = image_similarity_score(
                bool(lost["image_path"]), bool(found["image_path"]), loc_score > 0.6
            )

            scores = {
                "text": text_score,
                "image": img_score,
                "category": cat_score,
                "features": feat_score,
                "location": loc_score,
                "time": time_score,
                "brand_color": brand_color_score,
            }
            score = final_score(scores)
            results.append({
                "found": found,
                "scores": scores,
                "final": score,
                "label": label_for_score(score),
            })

    results.sort(key=lambda r: r["final"], reverse=True)
    return results[:top_k]
