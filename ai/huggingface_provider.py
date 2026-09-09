"""
ai/huggingface_provider.py

Hugging Face router provider (OpenAI-compatible /v1/chat/completions).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import requests

from .groq_provider import _extract_json  # shared, resilient JSON parser
from .provider import AIProvider
from .prompts import SYSTEM_EXPLANATION, SYSTEM_EXTRACTION


class HuggingFaceProvider(AIProvider):
    """Hugging Face router provider (OpenAI-compatible /v1/chat/completions)."""

    def _chat(self, messages: List[Dict[str, str]], temperature: float = 0.1,
              max_tokens: int = 1024, timeout: int = 45) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise TimeoutError("Hugging Face request timed out.") from exc
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(f"Could not reach Hugging Face: {exc}") from exc

        self.raise_for_status(resp.status_code, resp.text)
        return resp.json()["choices"][0]["message"]["content"]

    # ---- AIProvider interface ----

    def analyze_item(self, text: str, image_b64: Optional[str] = None) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": SYSTEM_EXTRACTION},
            {"role": "user", "content": f"Item report:\n{text}\n\nReturn JSON only."},
        ]
        return _extract_json(self._chat(messages))

    def generate_explanation(self, match_data: Dict[str, Any]) -> str:
        prompt = (
            "Verified match data (do not invent factors):\n"
            + json.dumps(match_data, default=str)
            + "\n\nExplain why these two items may match."
        )
        messages = [
            {"role": "system", "content": SYSTEM_EXPLANATION},
            {"role": "user", "content": prompt},
        ]
        try:
            return self._chat(messages, temperature=0.2)
        except Exception:
            return "Items share similar category, color, and location."

    def test_connection(self) -> Tuple[bool, str]:
        try:
            self._chat([{"role": "user", "content": "ping"}], max_tokens=5, timeout=15)
            return True, f"Connected - {self.model}"
        except Exception as exc:
            return False, str(exc)
