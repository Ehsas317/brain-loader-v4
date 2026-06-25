"""Universal provider router with per-role fallback chains."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .providers.base import BaseProvider, CallResult
from .providers.anthropic_provider import AnthropicProvider
from .providers.openai_provider import OpenAICompatibleProvider
from .providers.gemini_provider import GeminiProvider
from .providers.ollama_provider import OllamaProvider
from .providers.mlx_provider import MLXProvider

logger = logging.getLogger(__name__)

_RATE_LIMIT_SIGNALS = ("rate limit", "too many requests", "429", "ratelimit")
_QUOTA_SIGNALS = ("quota exceeded", "insufficient_quota", "billing", "credit", "payment")


@dataclass
class RouteResult:
    task_id: str
    role: str
    text: str
    provider: str
    model: str
    elapsed_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class RouterStats:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    provider_calls: Dict[str, int] = field(default_factory=dict)
    fallbacks: int = 0


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"
        self._lock = asyncio.Lock()

    async def record_success(self):
        # FIX BUG-V4-005: Shield against cancellation to ensure lock
        # is always released even if the task is cancelled mid-operation.
        with asyncio.shield_context():
            async with self._lock:
                self.failures = 0
                self.state = "closed"

    async def record_failure(self):
        # FIX BUG-V4-005: Shield against cancellation to ensure lock
        # is always released and state remains consistent.
        with asyncio.shield_context():
            async with self._lock:
                self.failures += 1
                self.last_failure_time = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = "open"
                    logger.warning("[CircuitBreaker] Provider OPENED after %d failures", self.failures)

    async def can_attempt(self) -> bool:
        async with self._lock:
            if self.state == "closed":
                return True
            if self.state == "open":
                if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                    self.state = "half-open"
                    return True
                return False
            return True


class UniversalRouter:
    _LOCAL = {"mlx", "ollama"}

    def __init__(self, config: dict):
        self.config = config
        self.stats = RouterStats()
        p = config.get("providers", {})

        cb_cfg = config.get("circuit_breaker", {})
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        self._providers: Dict[str, BaseProvider] = {
            "anthropic": AnthropicProvider(p.get("anthropic", {}).get("api_key", "")),
            "openai": OpenAICompatibleProvider(
                p.get("openai", {}).get("api_key", ""), provider_name="openai"
            ),
            "openrouter": OpenAICompatibleProvider(
                p.get("openrouter", {}).get("api_key", ""),
                base_url=p.get("openrouter", {}).get("base_url", "https://openrouter.ai/api/v1"),
                provider_name="openrouter",
            ),
            "groq": OpenAICompatibleProvider(
                p.get("groq", {}).get("api_key", ""),
                base_url="https://api.groq.com/openai/v1",
                provider_name="groq",
            ),
            "deepseek": OpenAICompatibleProvider(
                p.get("deepseek", {}).get("api_key", ""),
                base_url="https://api.deepseek.com/v1",
                provider_name="deepseek",
            ),
            "google": GeminiProvider(
                p.get("google", {}).get("api_key", ""),
                base_url=p.get("google", {}).get("base_url", "https://generativelanguage.googleapis.com/v1beta"),
            ),
            "ollama": OllamaProvider(p.get("ollama", {}).get("host", "http://localhost:11434")),
            "mlx": MLXProvider(enabled=p.get("mlx", {}).get("enabled", True)),
        }

        for name in self._providers:
            self.circuit_breakers[name] = CircuitBreaker(
                failure_threshold=cb_cfg.get("failure_threshold", 5),
                recovery_timeout=cb_cfg.get("recovery_timeout", 60),
            )

        self._local_locks: Dict[str, asyncio.Lock] = {
            "mlx": asyncio.Lock(),
            "ollama": asyncio.Lock(),
        }

    async def execute(
        self,
        role: str,
        task_id: str,
        prompt: str,
        system: str = "",
    ) -> RouteResult:
        role_cfg = self.config.get("roles", {}).get(role, {})
        chain: List[dict] = role_cfg.get("chain", [])
        max_tokens: int = role_cfg.get("max_tokens", 4096)
        temperature: float = role_cfg.get("temperature", 0.6)

        if not chain:
            return RouteResult(
                task_id=task_id, role=role, text="", provider="none", model="none",
                elapsed_s=0, success=False,
                error=f"No chain configured for role '{role}'. Add it to config.yaml.",
            )

        for idx, node in enumerate(chain):
            pname = node["provider"]
            model = node["model"]
            provider = self._providers.get(pname)

            if not provider:
                logger.warning("[Router] Unknown provider '%s', skipping", pname)
                continue

            if not provider.is_available():
                logger.debug("[Router] Provider '%s' not available, skipping", pname)
                continue

            cb = self.circuit_breakers.get(pname)
            if cb and not await cb.can_attempt():
                logger.debug("[Router] Provider '%s' circuit breaker OPEN, skipping", pname)
                continue

            if idx > 0:
                self.stats.fallbacks += 1
                logger.info("[Router] %s: fallback #%d → %s/%s", task_id, idx, pname, model)

            try:
                t0 = time.monotonic()

                if pname in self._LOCAL:
                    lock = self._local_locks[pname]
                    async with lock:
                        result = await provider.call(prompt, system, max_tokens, temperature, model)
                else:
                    result = await provider.call(prompt, system, max_tokens, temperature, model)

                elapsed = time.monotonic() - t0

                self.stats.total_input_tokens += result.input_tokens
                self.stats.total_output_tokens += result.output_tokens
                self.stats.total_cost_usd += result.cost_usd
                self.stats.provider_calls[pname] = self.stats.provider_calls.get(pname, 0) + 1

                if cb:
                    await cb.record_success()

                return RouteResult(
                    task_id=task_id, role=role,
                    text=result.text, provider=pname, model=model,
                    elapsed_s=elapsed,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_usd=result.cost_usd,
                    success=True,
                )

            except Exception as e:
                err = str(e).lower()
                if any(s in err for s in _QUOTA_SIGNALS):
                    logger.warning("[Router] Quota/billing on %s/%s — skipping immediately.", pname, model)
                elif any(s in err for s in _RATE_LIMIT_SIGNALS):
                    logger.warning("[Router] Rate-limited on %s/%s — waiting 2s.", pname, model)
                    await asyncio.sleep(2)
                else:
                    logger.warning("[Router] Error on %s/%s: %s", pname, model, e)

                if cb:
                    await cb.record_failure()
                continue

        return RouteResult(
            task_id=task_id, role=role, text="", provider="exhausted", model="none",
            elapsed_s=0, success=False,
            error=f"All providers in chain for role '{role}' failed.",
        )

    def get_stats(self) -> str:
        s = self.stats
        calls = " · ".join(f"{k}={v}" for k, v in s.provider_calls.items()) or "none yet"
        return (
            f"Tokens — in: {s.total_input_tokens:,}  out: {s.total_output_tokens:,}\n"
            f"Cost: ${s.total_cost_usd:.4f}   Fallbacks: {s.fallbacks}\n"
            f"Provider calls: {calls}"
        )
