"""Abstract base for all providers + result dataclasses."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class CallResult:
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def call(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
        model: str,
    ) -> CallResult:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...
