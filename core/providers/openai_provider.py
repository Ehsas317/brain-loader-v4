"""OpenAI, OpenRouter, Groq, DeepSeek provider (identical async API surface)."""
from __future__ import annotations
import logging
from typing import Optional

from .base import BaseProvider, CallResult

logger = logging.getLogger(__name__)

_PROVIDER_CONFIGS = {
    "openai": {"base_url": None, "input_rate": 2.50, "output_rate": 10.00},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "input_rate": 0.27, "output_rate": 0.85},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "input_rate": 0.50, "output_rate": 0.79},
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "input_rate": 0.14, "output_rate": 0.28},
}


class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, api_key: str, provider_name: str = "openai", base_url: Optional[str] = None):
        self.api_key = api_key
        self.name = provider_name
        self._client = None

        config = _PROVIDER_CONFIGS.get(provider_name, {})
        self.input_rate = config.get("input_rate", 1.0)
        self.output_rate = config.get("output_rate", 2.0)

        if api_key:
            try:
                from openai import AsyncOpenAI
                kwargs: dict = {"api_key": api_key}
                url = base_url or config.get("base_url")
                if url:
                    kwargs["base_url"] = url
                self._client = AsyncOpenAI(**kwargs)
            except ImportError:
                logger.warning(f"[{provider_name}] openai package not installed.")

    def is_available(self) -> bool:
        return bool(self.api_key and self._client)

    async def call(
        self, prompt: str, system: str, max_tokens: int, temperature: float, model: str
    ) -> CallResult:
        if not self._client:
            raise RuntimeError(f"{self.name} client not initialized.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        text = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        cost = (input_tokens / 1_000_000) * self.input_rate + (output_tokens / 1_000_000) * self.output_rate

        return CallResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
