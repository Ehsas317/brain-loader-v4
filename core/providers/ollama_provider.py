#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/providers/ollama_provider.py                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Ollama Provider — local Ollama server integration for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Ollama Provider

Local Ollama server integration.
"""

import logging
import httpx
from core.providers.base import BaseProvider

logger = logging.getLogger("surge.providers.ollama")


class OllamaProvider(BaseProvider):
    """
    Ollama provider for Surge.

    Usage:
        provider = OllamaProvider(config)
        result = provider.generate("Write code...")
    """

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using Ollama API."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.0},
            }
            resp = httpx.post(f"{self.endpoint}/api/generate",
                            json=payload, timeout=120.0)
            resp.raise_for_status()
            return resp.json()["response"]
        except Exception as e:
            logger.error("Ollama generation failed: %s", e)
            return f"[Ollama Error: {e}]"

    def health_check(self) -> bool:
        """Check Ollama server availability."""
        try:
            resp = httpx.get(f"{self.endpoint}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
