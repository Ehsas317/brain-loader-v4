#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/providers/base.py                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Base provider class defining the interface for all LLM providers.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Base Provider

Abstract base class for all LLM provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProvider(ABC):
    """Base class for all LLM providers in Surge."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "")
        self.endpoint = config.get("endpoint", "")
        self.api_key = config.get("api_key", "")

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate text completion. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is available. Must be implemented by subclasses."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} model={self.model}>"
