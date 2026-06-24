"""Cost Tracker — Session-level API spend monitoring."""
from __future__ import annotations
import json
import logging
import threading
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class CostTracker:
    def __init__(self, outputs_dir: str = "./outputs"):
        self.outputs_dir = Path(outputs_dir)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self._costs: Dict[str, float] = {}
        self._total_tokens = {"input": 0, "output": 0}
        self._lock = threading.Lock()

    def add_request(self, provider: str, model: str, input_tokens: int,
                    output_tokens: int, cost_usd: float):
        key = f"{provider}/{model}"
        with self._lock:
            self._costs[key] = self._costs.get(key, 0.0) + cost_usd
            self._total_tokens["input"] += input_tokens
            self._total_tokens["output"] += output_tokens
        logger.debug("[CostTracker] %s: $%.4f (total: $%.4f)",
                     key, cost_usd, self.get_total())

    def get_total(self) -> float:
        with self._lock:
            return sum(self._costs.values())

    def get_summary(self) -> Dict:
        with self._lock:
            return {
                "total_usd": round(sum(self._costs.values()), 4),
                "by_provider_model": {k: round(v, 4) for k, v in self._costs.items()},
                "total_tokens": self._total_tokens.copy(),
            }

    def check_budget(self, warn_threshold: float, max_threshold: float) -> str:
        total = self.get_total()
        if total >= max_threshold:
            return "exceeded"
        if total >= warn_threshold:
            return "warn"
        return "ok"

    def save_report(self, project_name: str):
        report_file = self.outputs_dir / f"cost_report_{project_name}.json"
        with open(report_file, "w") as f:
            json.dump(self.get_summary(), f, indent=2)
        logger.info("[CostTracker] Report saved: %s", report_file)

    def reset(self):
        with self._lock:
            self._costs.clear()
            self._total_tokens = {"input": 0, "output": 0}
