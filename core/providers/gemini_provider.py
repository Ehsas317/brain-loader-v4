"""Google Gemini provider."""
from __future__ import annotations
import logging

import requests

from .base import BaseProvider, CallResult

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    name = "google"

    def __init__(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def call(
        self, prompt: str, system: str, max_tokens: int, temperature: float, model: str
    ) -> CallResult:
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        if system:
            contents.insert(0, {"role": "user", "parts": [{"text": f"System: {system}"}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

        cost = (input_tokens / 1_000_000) * 1.25 + (output_tokens / 1_000_000) * 10.00

        return CallResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
