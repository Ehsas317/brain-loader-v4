"""Ollama local provider — any system."""
from __future__ import annotations
import logging
import re

import aiohttp

from .base import BaseProvider, CallResult

logger = logging.getLogger(__name__)


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host.rstrip("/")

    def is_available(self) -> bool:
        import requests
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    async def call(
        self, prompt: str, system: str, max_tokens: int, temperature: float, model: str
    ) -> CallResult:
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        timeout = aiohttp.ClientTimeout(total=600)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{self.host}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                text = _strip_think(data.get("response", ""))

        return CallResult(text=text, provider=self.name, model=model)
