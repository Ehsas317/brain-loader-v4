#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/providers/gemini_provider.py                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Google Gemini Provider — Gemini API integration for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Gemini Provider

Google Gemini API integration.
"""

import logging
import httpx
from core.providers.base import BaseProvider

logger = logging.getLogger("surge.providers.gemini")


class GeminiProvider(BaseProvider):
    """
    Google Gemini provider for Surge.

    Usage:
        provider = GeminiProvider(config)
        result = provider.generate("Write code...")
    """

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using Gemini API."""
        try:
            url = f"{self.endpoint}/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            }
            resp = httpx.post(url, params=params, json=payload, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error("Gemini generation failed: %s", e)
            return f"[Gemini Error: {e}]"

    def health_check(self) -> bool:
        """Check Gemini API availability."""
        try:
            url = f"{self.endpoint}/models"
            params = {"key": self.api_key}
            resp = httpx.get(url, params=params, timeout=10.0)
            return resp.status_code == 200
        except Exception:
            return False
