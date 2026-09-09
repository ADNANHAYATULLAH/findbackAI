"""
ai/embeddings.py

Sentence-embedding generation and FAISS index persistence.

The embedding model is loaded once per Streamlit process via
`st.cache_resource`. FAISS reads/writes go through a module-level lock
since Streamlit can run multiple script reruns/sessions against the same
process, and FAISS's on-disk index is not safe for concurrent writers.
"""

from __future__ import annotations

import json
import os
import threading
from typing import List, Tuple

import faiss
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 384
FAISS_PATH = "vector_store/index.faiss"
META_PATH = "vector_store/metadata.json"

_faiss_lock = threading.Lock()


@st.cache_resource(show_spinner=False)
def load_embedding_model() -> SentenceTransformer:
    """Load (once per process) the sentence-transformer used for semantic
    matching. Cached with `st.cache_resource` so reruns don't reload weights."""
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def build_text_for_embedding(
    title: str, desc: str, brand: str, color: str, features: str, location: str
) -> str:
    """Compose the canonical text blob embedded for both indexing and search
    so lost/found queries stay comparable."""
    return f"{title}. {desc}. Brand {brand}. Color {color}. Features {features}. Location {location}".strip()


def get_embedding(text: str) -> np.ndarray:
    """Return a normalized float32 embedding for `text`."""
    model = load_embedding_model()
    emb = model.encode(text, normalize_embeddings=True)
    return emb.astype("float32")


def load_faiss() -> Tuple[faiss.Index, List[int]]:
    """Load the FAISS index and its parallel id list from disk.

    Returns an empty flat index if nothing has been persisted yet. Falls
    back to a fresh empty index if the on-disk files are corrupt, rather
    than crashing item creation / matching.
    """
    os.makedirs("vector_store", exist_ok=True)
    with _faiss_lock:
        if os.path.exists(FAISS_PATH):
            try:
                index = faiss.read_index(FAISS_PATH)
                meta = json.load(open(META_PATH)) if os.path.exists(META_PATH) else []
                return index, meta
            except Exception:
                pass  # fall through to a fresh index below
        return faiss.IndexFlatIP(EMBEDDING_DIM), []


def save_faiss(index: faiss.Index, meta: List[int]) -> None:
    """Persist the FAISS index and id list to disk under a lock."""
    os.makedirs("vector_store", exist_ok=True)
    with _faiss_lock:
        faiss.write_index(index, FAISS_PATH)
        with open(META_PATH, "w") as fh:
            json.dump(meta, fh)


def add_to_index(item_id: int, embedding: np.ndarray) -> None:
    """Append one embedding to the persisted FAISS index."""
    index, meta = load_faiss()
    index.add(np.array([embedding]).astype("float32"))
    meta.append(item_id)
    save_faiss(index, meta)


def rebuild_from_db(embeddings_list: List[np.ndarray], ids: List[int]) -> faiss.Index:
    """Rebuild the FAISS index from scratch (e.g. after a data migration)."""
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    if embeddings_list:
        mat = np.vstack(embeddings_list).astype("float32")
        index.add(mat)
    save_faiss(index, ids)
    return index
