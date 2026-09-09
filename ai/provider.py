"""
ai/provider.py

Abstract base class every AI provider (Groq, HuggingFace, ...) implements,
plus a small typed exception hierarchy so callers (services/provider_service.py)
can make precise fallback decisions instead of pattern-matching error strings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class ProviderError(Exception):
    """Base class for all provider-related failures."""


class ProviderAuthError(ProviderError):
    """Raised on HTTP 401 - invalid or missing API key. Never worth retrying
    with the same key; fallback to another provider or ask the user to fix it."""


class ProviderRateLimitError(ProviderError):
    """Raised on HTTP 429 - safe (and expected) to fail over to a backup
    provider or rule-based extraction."""


class ProviderServerError(ProviderError):
    """Raised on HTTP 5xx - provider is down/unstable; fail over."""


class AIProvider(ABC):
    """Common interface implemented by every concrete provider integration."""

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def raise_for_status(status_code: int, body: str) -> None:
        """Translate an HTTP status code into a typed ProviderError.

        No-op for 2xx / other non-error codes so callers can call this
        unconditionally before parsing the response.
        """
        if status_code == 401:
            raise ProviderAuthError("Invalid or missing API key (401).")
        if status_code == 429:
            raise ProviderRateLimitError("Rate limited by provider (429).")
        if status_code >= 500:
            raise ProviderServerError(f"Provider server error ({status_code}).")
        if status_code >= 400:
            raise ProviderError(f"Provider request failed ({status_code}): {body[:200]}")

    @abstractmethod
    def analyze_item(self, text: str, image_b64: Optional[str] = None) -> Dict[str, Any]:
        """Extract structured attributes (category, brand, color, ...) from a
        free-text item description. Must return a dict; raise a ProviderError
        subclass on failure so the caller can decide whether to fail over."""

    @abstractmethod
    def generate_explanation(self, match_data: Dict[str, Any]) -> str:
        """Produce a short human-readable explanation of a match, grounded
        only in the numeric scores/fields passed in `match_data`."""

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Return (ok, message) describing whether this provider is reachable
        with the current credentials. Should never raise."""
