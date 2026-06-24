"""MLX local provider — Apple Silicon only."""
from __future__ import annotations
import asyncio
import gc
import logging
import re

from .base import BaseProvider, CallResult

logger = logging.getLogger(__name__)


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class MLXProvider(BaseProvider):
    name = "mlx"

    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._model = None
        self._tokenizer = None
        self._current_path: str = ""

    def is_available(self) -> bool:
        if not self._enabled:
            return False
        try:
            import mlx.core
            return True
        except ImportError:
            return False

    def _load(self, model_path: str) -> None:
        if self._current_path == model_path and self._model is not None:
            return

        if self._model is not None:
            del self._model
            del self._tokenizer
            self._model = None
            self._tokenizer = None
            gc.collect()
            try:
                import mlx.core as mx
                mx.metal.clear_cache()
            except Exception:
                pass

        from mlx_lm import load
        self._model, self._tokenizer = load(model_path)
        self._current_path = model_path

    def _sync_call(
        self, prompt: str, system: str, max_tokens: int, temperature: float, model_path: str
    ) -> CallResult:
        from mlx_lm import generate

        self._load(model_path)

        if (
            hasattr(self._tokenizer, "apply_chat_template")
            and self._tokenizer.chat_template
        ):
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            formatted = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            formatted = f"System: {system}\n\nUser: {prompt}\n\nAssistant:" if system else f"User: {prompt}\n\nAssistant:"

        output = generate(
            self._model,
            self._tokenizer,
            prompt=formatted,
            max_tokens=max_tokens,
            temp=temperature,
            verbose=False,
        )

        return CallResult(
            text=_strip_think(output),
            provider=self.name,
            model=model_path,
        )

    async def call(
        self, prompt: str, system: str, max_tokens: int, temperature: float, model: str
    ) -> CallResult:
        if not self.is_available():
            raise RuntimeError("MLX not available (install mlx and mlx-lm, requires Apple Silicon).")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_call, prompt, system, max_tokens, temperature, model
        )
