"""
database/database.py

Low-level SQLite connection handling and schema management.

Prefer `get_connection()`, a context manager that opens a short-lived
connection with WAL journaling enabled (so concurrent Streamlit
reruns/tabs don't hit "database is locked" errors) and always closes
safely, even on exceptions.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

DB_PATH = "findback.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection configured for concurrent Streamlit access.

    Usage:
        with get_connection() as conn:
            conn.execute(...)
            conn.commit()

    The connection is always closed on exit. Commit is the caller's
    responsibility so read-only callers don't pay for an unnecessary commit.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=8000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
    finally:
        conn.close()


def get_conn() -> sqlite3.Connection:
    """Backward-compatible raw-connection accessor.

    Prefer `get_connection()` (context manager) in new code. Kept for
    simple read-only call sites; the caller is responsible for closing it.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=8000;")
    return conn


def init_db() -> None:
    """Create tables and indexes if they do not already exist. Idempotent."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                type TEXT CHECK(type IN ('lost','found')),
                title TEXT, description TEXT, category TEXT, brand TEXT,
                primary_color TEXT, location TEXT, event_date TEXT, event_time TEXT,
                image_path TEXT, status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS item_features(
                item_id INTEGER PRIMARY KEY,
                ai_category TEXT, ai_brand TEXT, ai_colors TEXT,
                ai_features TEXT, ai_visible_text TEXT, ai_condition TEXT,
                ai_confidence TEXT, embedding_reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES items(id)
            );
            CREATE TABLE IF NOT EXISTS matches(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lost_item_id INTEGER, found_item_id INTEGER,
                text_score REAL, image_score REAL, category_score REAL,
                feature_score REAL, location_score REAL, time_score REAL,
                brand_color_score REAL, final_score REAL,
                explanation TEXT, status TEXT DEFAULT 'potential',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS claims(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lost_item_id INTEGER NOT NULL,
                found_item_id INTEGER NOT NULL,
                requested_by_user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'potential',
                verification_status TEXT DEFAULT 'pending',
                handover_status TEXT DEFAULT 'pending',
                notes TEXT,
                reviewed_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                UNIQUE(lost_item_id, found_item_id),
                FOREIGN KEY(lost_item_id) REFERENCES items(id),
                FOREIGN KEY(found_item_id) REFERENCES items(id),
                FOREIGN KEY(requested_by_user_id) REFERENCES users(id),
                FOREIGN KEY(reviewed_by_user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS ai_usage(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT, model TEXT, request_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success INTEGER, error_type TEXT, latency_ms INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
            CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
            CREATE INDEX IF NOT EXISTS idx_match_pair ON matches(lost_item_id, found_item_id);
            CREATE INDEX IF NOT EXISTS idx_matches_lost ON matches(lost_item_id);
            CREATE INDEX IF NOT EXISTS idx_matches_found ON matches(found_item_id);
            CREATE INDEX IF NOT EXISTS idx_claims_lost ON claims(lost_item_id);
            CREATE INDEX IF NOT EXISTS idx_claims_found ON claims(found_item_id);
            CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
            """
        )
        conn.commit()

        # Migration for older SQLite databases created before we added user and claim tables.
        item_columns = [row[1] for row in conn.execute("PRAGMA table_info(items)").fetchall()]
        if "user_id" not in item_columns:
            conn.execute("ALTER TABLE items ADD COLUMN user_id INTEGER DEFAULT 1")

        user_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
        if not user_columns:
            conn.execute(
                "CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, full_name TEXT, role TEXT NOT NULL, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )

        claim_columns = [row[1] for row in conn.execute("PRAGMA table_info(claims)").fetchall()]
        if not claim_columns:
            conn.execute(
                "CREATE TABLE claims(id INTEGER PRIMARY KEY AUTOINCREMENT, lost_item_id INTEGER NOT NULL, found_item_id INTEGER NOT NULL, requested_by_user_id INTEGER NOT NULL, status TEXT DEFAULT 'potential', verification_status TEXT DEFAULT 'pending', handover_status TEXT DEFAULT 'pending', notes TEXT, reviewed_by_user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, resolved_at TIMESTAMP, UNIQUE(lost_item_id, found_item_id))"
            )
        conn.commit()

    from database.queries import seed_default_users

    seed_default_users()
