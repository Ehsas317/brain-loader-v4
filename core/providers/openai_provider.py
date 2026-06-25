#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/providers/openai_provider.py                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   OpenAI-compatible Provider — works with OpenAI, DeepSeek, Mistral,
#   and any other OpenAI-compatible API endpoint.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — OpenAI-Compatible Provider

Works with OpenAI, DeepSeek, Mistral, and compatible APIs.
"""

import logging
import httpx
from core.providers.base import BaseProvider

logger = logging.getLogger("surge.providers.openai")


class OpenAIProvider(BaseProvider):
    """
    OpenAI-compatible provider for Surge.

    Works with OpenAI, DeepSeek, Mistral, Together, and other
    OpenAI-compatible endpoints.

    Usage:
        provider = OpenAIProvider(config)
        result = provider.generate("Write code...")
    """

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using OpenAI-compatible API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }
            resp = httpx.post(f"{self.endpoint}/chat/completions",
                            headers=headers, json=payload, timeout=60.0)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("OpenAI-compatible generation failed: %s", e)
            return f"[OpenAI Error: {e}]"

    def health_check(self) -> bool:
        """Check API availability."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = httpx.get(f"{self.endpoint}/models", headers=headers, timeout=10.0)
            return resp.status_code == 200
        except Exception:
            return False
