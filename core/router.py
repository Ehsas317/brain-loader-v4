#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/router.py                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Model Router — routes tasks to the optimal LLM provider based on
#   task type, cost, availability, and configured priorities.
#
# HOW TO USE SURGE:
#   1. Install:    pip install -r requirements.txt
#   2. Configure:  Edit config.yaml with your API tokens
#   3. Run:        python main.py "Your project description"
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Model Router

Routes tasks to optimal LLM providers based on type, cost, and availability.
"""

import asyncio
import logging
from typing import Dict, Optional

import httpx

logger = logging.getLogger("surge.router")


class ModelRouter:
    """
    Surge Model Router

    Routes generation requests to the optimal provider based on:
    - Task type and provider capabilities
    - Cost per token
    - Provider availability
    - Configured priority

    Usage:
        router = ModelRouter(providers)
        provider = router.route("frontend")
        result = router.generate(provider, "Write React code...")
    """

    def __init__(self, providers: Dict[str, Dict]):
        self.providers = providers
        self.routing_rules = {}
        logger.info("[Router] Initialized with %d providers", len(providers))

    def route(self, task_type: str) -> Optional[str]:
        """Select the best provider for a task type."""
        available = [p for p, cfg in self.providers.items()
                     if cfg.get("api_key") or cfg.get("type") == "local"]

        if not available:
            logger.error("[Router] No providers available")
            return None

        # Sort by priority (lower = better)
        available.sort(key=lambda p: self.providers[p].get("priority", 99))

        best = available[0]
        logger.debug("[Router] Routed %s → %s", task_type, best)
        return best

    def generate(self, provider_name: str, prompt: str, max_tokens: int = 4096) -> str:
        """Generate text using the specified provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        cfg = self.providers[provider_name]

        # Handle local MLX
        if cfg.get("type") == "local":
            return self._local_generate(cfg, prompt, max_tokens)

        # Handle cloud API
        return self._cloud_generate(cfg, prompt, max_tokens)

    def _local_generate(self, cfg: Dict, prompt: str, max_tokens: int) -> str:
        """Generate using local MLX model."""
        try:
            from mlx_lm import load, generate
            model, tokenizer = load(cfg["path"])
            return generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens, temp=0.0)
        except Exception as e:
            logger.error("Local generation failed: %s", e)
            return f"[Local Error: {e}]"

    def _cloud_generate(self, cfg: Dict, prompt: str, max_tokens: int) -> str:
        """Generate using cloud API."""
        try:
            headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
            payload = {
                "model": cfg["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }
            resp = httpx.post(f"{cfg['endpoint']}/chat/completions",
                            headers=headers, json=payload, timeout=60.0)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Cloud generation failed for %s: %s", cfg.get("model"), e)
            return f"[Cloud Error: {e}]"

    def __repr__(self):
        return f"<ModelRouter providers={list(self.providers.keys())}>"
