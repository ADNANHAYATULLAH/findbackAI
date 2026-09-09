"""
utils/security.py

Small security-adjacent helpers: filename sanitization for uploads, API-key
masking for display, and an allowlist check for user-editable endpoints.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid

ALLOWED_ENDPOINTS = ["https://api.groq.com/", "https://router.huggingface.co/"]


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 for secure storage."""
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    if not stored_hash or not stored_hash.startswith("pbkdf2_sha256$"):
        return False
    _, salt_hex, digest_hex = stored_hash.split("$", 2)
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return hmac_compare(derived, expected)


def hmac_compare(left: bytes, right: bytes) -> bool:
    """Constant-time compare for secret values."""
    return secrets_compare(left, right)


def secrets_compare(left: bytes, right: bytes) -> bool:
    """Perform a constant-time byte comparison."""
    if len(left) != len(right):
        return False
    result = 0
    for a, b in zip(left, right):
        result |= a ^ b
    return result == 0


def sanitize_filename(name: str) -> str:
    """Strip directory components and unsafe characters, then prefix with a
    UUID so uploaded filenames can never collide or be used for path
    traversal."""
    name = os.path.basename(name)
    name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
    return f"{uuid.uuid4().hex}_{name[-30:]}"


def mask_key(key: str) -> str:
    """Return a display-safe masked form of an API key (last 4 chars only)."""
    if not key or len(key) < 8:
        return "••••••••"
    return "••••••••••••" + key[-4:]


def validate_endpoint(url: str) -> bool:
    """Reject any user-supplied base URL that isn't a known provider host.
    Prevents the "Endpoint" field in Settings from being used as an SSRF
    vector to send API keys to an arbitrary server."""
    return any(url.startswith(allowed) for allowed in ALLOWED_ENDPOINTS)
