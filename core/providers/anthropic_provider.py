#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/providers/anthropic_provider.py                   ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Anthropic Provider — Claude API integration for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Anthropic Provider

Claude API integration for high-quality generation.
"""

import logging
import httpx
from core.providers.base import BaseProvider

logger = logging.getLogger("surge.providers.anthropic")


class AnthropicProvider(BaseProvider):
    """
    Anthropic Claude provider for Surge.

    Usage:
        provider = AnthropicProvider(config)
        result = provider.generate("Write Python code...")
    """

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using Claude API."""
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            resp = httpx.post(f"{self.endpoint}/messages",
                            headers=headers, json=payload, timeout=60.0)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
        except Exception as e:
            logger.error("Anthropic generation failed: %s", e)
            return f"[Anthropic Error: {e}]"

    def health_check(self) -> bool:
        """Check Anthropic API availability."""
        try:
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
            resp = httpx.get(f"{self.endpoint}/models", headers=headers, timeout=10.0)
            return resp.status_code == 200
        except Exception:
            return False
