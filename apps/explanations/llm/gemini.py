"""Minimal Gemini REST client (generateContent). No retries: on the free tier every request is precious."""
import re
from typing import Any, Dict, Optional
import requests
from .base import LLMError, LLMRateLimited

class GeminiClient:
    def __init__(self, api_key: str, model: str, base_url: str, timeout: float, max_output_tokens: int, temperature: float):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature

    def generate_json(self, system: str, prompt: str) -> str:
        url = f"{self.base_url}/models/{self.model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
                "responseMimeType": "application/json",
            },
        }
        try:
            response = requests.post(
                url, json=body, headers={"x-goog-api-key": self.api_key}, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise LLMError(f"network error: {exc.__class__.__name__}") from exc

        if response.status_code == 429:
            raise self._rate_limited(response)
        if response.status_code >= 400:
            raise LLMError(f"Gemini returned HTTP {response.status_code}")
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: requests.Response) -> str:
        try:
            data = response.json()
            candidate = data["candidates"][0]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMError("no candidates in Gemini response (possibly blocked)") from exc
        if candidate.get("finishReason") not in (None, "STOP"):
            raise LLMError(f"generation ended with {candidate.get('finishReason')}")
        parts = candidate.get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text.strip():
            raise LLMError("empty response")
        return text

    @staticmethod
    def _rate_limited(response: requests.Response) -> LLMRateLimited:
        retry_after: Optional[float] = None
        daily = False
        try:
            details: list[Dict[str, Any]] = response.json().get("error", {}).get("details", [])
        except ValueError:
            details = []
        for detail in details:
            kind = detail.get("@type", "")
            if kind.endswith("RetryInfo"):
                match = re.match(r"([\d.]+)s", str(detail.get("retryDelay", "")))
                if match:
                    retry_after = float(match.group(1))
            if kind.endswith("QuotaFailure"):
                if any("PerDay" in v.get("quotaId", "") for v in detail.get("violations", [])):
                    daily = True
        header = response.headers.get("Retry-After")
        if retry_after is None and header and header.isdigit():
            retry_after = float(header)
        return LLMRateLimited("Gemini rate limit hit", retry_after=retry_after, daily=daily)
