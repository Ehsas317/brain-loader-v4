#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/providers/mlx_provider.py                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   MLX Provider — local Apple Silicon MLX model integration for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — MLX Provider

Local MLX model integration for Apple Silicon.
"""

import logging
from pathlib import Path
from core.providers.base import BaseProvider

logger = logging.getLogger("surge.providers.mlx")


class MLXProvider(BaseProvider):
    """
    Local MLX provider for Surge (Apple Silicon).

    Usage:
        provider = MLXProvider(config)
        result = provider.generate("Write code...")
    """

    def __init__(self, config):
        super().__init__(config)
        self.model_path = config.get("path", "")
        self.model = None
        self.tokenizer = None

    def _load(self):
        """Lazy-load the model."""
        if self.model is None:
            from mlx_lm import load
            if Path(self.model_path).exists():
                self.model, self.tokenizer = load(self.model_path)
            else:
                raise FileNotFoundError(f"Model not found: {self.model_path}")

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using local MLX model."""
        try:
            self._load()
            from mlx_lm import generate
            return generate(self.model, self.tokenizer, prompt=prompt,
                          max_tokens=max_tokens, temp=0.0)
        except Exception as e:
            logger.error("MLX generation failed: %s", e)
            return f"[MLX Error: {e}]"

    def health_check(self) -> bool:
        """Check if MLX model is available."""
        return Path(self.model_path).exists()
