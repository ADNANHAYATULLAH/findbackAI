"""
ai/groq_provider.py

Groq (OpenAI-compatible) chat-completions integration used for attribute
extraction and match explanations.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple

import requests

from .provider import AIProvider
from .prompts import SYSTEM_EXPLANATION, SYSTEM_EXTRACTION

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Dict[str, Any]:
    """Best-effort extraction of a JSON object from an LLM response.

    Handles: clean JSON, JSON wrapped in ```json ... ``` fences, and JSON
    embedded in surrounding prose. Never raises - returns {} on failure so
    callers can fall back to rule-based extraction instead of crashing.
    """
    if not text:
        return {}
    fence_match = _JSON_FENCE_RE.search(text)
    candidate = fence_match.group(1) if fence_match else text
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        pass
    obj_match = _JSON_OBJECT_RE.search(candidate)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


class GroqProvider(AIProvider):
    """Groq-hosted model access via the OpenAI-compatible /v1 API."""

    def _post(self, path: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise TimeoutError("Groq request timed out.") from exc
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(f"Could not reach Groq: {exc}") from exc

        self.raise_for_status(resp.status_code, resp.text)
        return resp.json()

    def analyze_item(self, text: str, image_b64: Optional[str] = None) -> Dict[str, Any]:
        # Note: the default text model (gpt-oss-20b) is text-only. For
        # vision-based extraction, swap to a vision-capable model such as
        # llama-3.2-11b-vision-preview and attach `image_b64` as an image_url part.
        messages = [
            {"role": "system", "content": SYSTEM_EXTRACTION},
            {"role": "user", "content": f"Item report:\n{text}\n\nReturn JSON only."},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        data = self._post("/chat/completions", payload)
        content = data["choices"][0]["message"]["content"]
        return _extract_json(content)

    def generate_explanation(self, match_data: Dict[str, Any]) -> str:
        prompt = f"Match data (do not invent): {json.dumps(match_data, default=str)}\nGenerate explanation."
        messages = [
            {"role": "system", "content": SYSTEM_EXPLANATION},
            {"role": "user", "content": prompt},
        ]
        try:
            data = self._post(
                "/chat/completions",
                {"model": self.model, "messages": messages, "temperature": 0.2},
            )
            return data["choices"][0]["message"]["content"]
        except Exception:
            return "Match based on text, category, location and time similarity."

    def test_connection(self) -> Tuple[bool, str]:
        try:
            self.analyze_item("test black bag")
            return True, f"Connected - Model {self.model}"
        except Exception as exc:  # surfaced verbatim to the Settings page
            return False, str(exc)
