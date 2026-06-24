"""Anthropic Claude provider."""
from __future__ import annotations
import logging

from .base import BaseProvider, CallResult

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        if api_key:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=api_key)
            except ImportError:
                logger.warning("[Anthropic] anthropic package not installed.")

    def is_available(self) -> bool:
        return bool(self.api_key and self._client)

    async def call(
        self, prompt: str, system: str, max_tokens: int, temperature: float, model: str
    ) -> CallResult:
        if not self._client:
            raise RuntimeError("Anthropic client not initialized.")

        response = await self._client.messages.create(
            model=model,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        text = response.content[0].text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = self._estimate_cost(model, input_tokens, output_tokens)

        return CallResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = {
            "claude-3-5-sonnet": (3.00, 15.00),
            "claude-3-5-haiku": (0.25, 1.25),
            "claude-3-opus": (15.00, 75.00),
        }
        input_rate, output_rate = pricing.get(model.split("-")[0] + "-" + model.split("-")[1], (3.00, 15.00))
        return (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate
