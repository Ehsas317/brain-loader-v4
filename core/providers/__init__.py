#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/providers/__init__.py                              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Provider package initializer for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Provider Package

LLM provider implementations for multi-backend dispatch.
"""

from core.providers.anthropic_provider import AnthropicProvider
from core.providers.openai_provider import OpenAIProvider
from core.providers.gemini_provider import GeminiProvider
from core.providers.mlx_provider import MLXProvider
from core.providers.ollama_provider import OllamaProvider
from core.providers.base import BaseProvider

__all__ = [
    "AnthropicProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "MLXProvider",
    "OllamaProvider",
    "BaseProvider",
]
