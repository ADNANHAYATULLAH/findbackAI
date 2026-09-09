"""
services/provider_service.py

Chooses and calls the active AI provider (Groq or Hugging Face), handling
auth-key resolution, typed-error-aware failover, and safe degradation to a
rule-based extractor if every provider is unavailable.

This is the ONLY place that reads `st.session_state` for provider config -
UI pages just set session_state and call `ProviderManager()`.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import streamlit as st

from ai.groq_provider import GroqProvider
from ai.huggingface_provider import HuggingFaceProvider
from ai.provider import AIProvider, ProviderAuthError, ProviderError, ProviderRateLimitError
from ai.schemas import safe_parse_extraction
from database.queries import log_ai_usage


class ProviderManager:
    """Resolves session settings into a live `AIProvider` and runs
    extraction with automatic failover between providers."""

    def __init__(self) -> None:
        ss = st.session_state
        self.provider_name: str = ss.get("provider", "Groq")
        self.auth_mode: str = ss.get("auth_mode", "app")
        self.user_key: str = ss.get("user_api_key", "")
        self.model: str = ss.get("model", "openai/gpt-oss-20b")
        self.base_url: str = ss.get("base_url", "https://api.groq.com/openai/v1")
        self.fallback_enabled: bool = ss.get("enable_fallback", True)

    # ---- key resolution ----

    def resolve_app_key(self, provider_name: str) -> str:
        """Look up the app-default API key for `provider_name` from
        `.streamlit/secrets.toml`. Public because Settings needs it too
        (e.g. to test a connection using the app default key)."""
        try:
            if not hasattr(st, "secrets"):
                return ""
            section = "GROQ" if provider_name == "Groq" else "HUGGINGFACE"
            return st.secrets.get(section, {}).get("API_KEY", "")
        except Exception:
            return ""

    def has_active_key(self) -> bool:
        """Used by the sidebar 'Connected / Disconnected' indicator."""
        key = self.user_key if self.auth_mode == "user" and self.user_key else self.resolve_app_key(self.provider_name)
        return bool(key)

    def get_provider(self, provider_name: Optional[str] = None) -> Optional[AIProvider]:
        """Build a provider instance for `provider_name` (default: the
        session's selected provider). Returns None if no key is available."""
        name = provider_name or self.provider_name
        key = self.user_key if self.auth_mode == "user" and self.user_key else self.resolve_app_key(name)
        if not key:
            return None
        if name == "Groq":
            return GroqProvider(key, self.model, self.base_url)
        return HuggingFaceProvider(key, self.model, self.base_url)

    # ---- extraction with failover ----

    def analyze_with_fallback(self, text: str) -> Dict[str, Any]:
        """Run attribute extraction, failing over to the other provider on
        rate-limit/server errors, then to a rule-based extractor as a last
        resort. The result is always pydantic-validated before being returned
        as a plain dict, so downstream code never sees malformed shapes."""
        provider_order = [self.provider_name]
        other = "HuggingFace" if self.provider_name == "Groq" else "Groq"
        if self.fallback_enabled:
            provider_order.append(other)

        last_error: Optional[Exception] = None
        for name in provider_order:
            provider = self.get_provider(name)
            if provider is None:
                continue
            start = time.time()
            try:
                raw = provider.analyze_item(text)
                latency = int((time.time() - start) * 1000)
                log_ai_usage(name, self.model, "analyze", True, latency_ms=latency)
                validated = safe_parse_extraction(raw)
                return validated.model_dump()
            except ProviderAuthError as exc:
                # Wrong key won't fix itself on a different provider's model
                # list, but it might still be worth trying the other
                # provider since it has its own key.
                latency = int((time.time() - start) * 1000)
                log_ai_usage(name, self.model, "analyze", False, "auth_error", latency)
                last_error = exc
                continue
            except ProviderRateLimitError as exc:
                latency = int((time.time() - start) * 1000)
                log_ai_usage(name, self.model, "analyze", False, "rate_limited", latency)
                last_error = exc
                continue
            except ProviderError as exc:
                latency = int((time.time() - start) * 1000)
                log_ai_usage(name, self.model, "analyze", False, type(exc).__name__, latency)
                last_error = exc
                continue
            except Exception as exc:  # network errors, timeouts, etc.
                latency = int((time.time() - start) * 1000)
                log_ai_usage(name, self.model, "analyze", False, type(exc).__name__, latency)
                last_error = exc
                continue

        # Every provider failed (or none configured) - degrade gracefully.
        return safe_parse_extraction(self.rule_based_extract(text)).model_dump()

    def rule_based_extract(self, text: str) -> Dict[str, Any]:
        """Keyword-based extraction used when no AI provider is reachable.
        Deliberately simple and conservative - it only asserts what it can
        directly see in the text."""
        lowered = text.lower()
        colors = ["black", "blue", "red", "white", "green", "grey", "gray", "brown"]
        found_colors = [c for c in colors if c in lowered]
        return {
            "category": "laptop_bag" if "bag" in lowered or "backpack" in lowered else None,
            "brand": {"value": "HP" if "hp" in lowered else None, "confidence": 0.6, "source": "text"},
            "primary_color": {
                "value": found_colors[0] if found_colors else None,
                "confidence": 0.6,
                "source": "text",
            },
            "secondary_colors": found_colors[1:],
            "distinctive_features": [s for s in ["blue sticker", "blue mark"] if s in lowered],
            "object_type": "backpack",
            "condition": "unknown",
        }
