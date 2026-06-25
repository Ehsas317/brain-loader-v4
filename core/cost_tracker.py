#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/cost_tracker.py                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Cost Tracker — monitors API usage costs across all providers.
#   Tracks spending per project and enforces budget limits.
#
# HOW TO USE SURGE:
#   1. Install:    pip install -r requirements.txt
#   2. Configure:  Edit config.yaml with your API tokens
#   3. Run:        python main.py "Your project description"
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Cost Tracker

Monitors API usage costs and enforces budget limits.
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("surge.cost")


@dataclass
class CostRecord:
    """Cost record for a single API call."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: str = ""


class CostTracker:
    """
    Surge Cost Tracker

    Tracks API usage costs across all providers and enforces
    budget limits. Alerts when approaching budget threshold.

    Usage:
        tracker = CostTracker(budget_limit=10.0, alert_threshold=0.8)
        tracker.record_call("deepseek", "deepseek-chat", 1000, 500, 0.01)
        if tracker.is_over_budget():
            print("Budget exceeded!")
    """

    def __init__(self, budget_limit: float = 10.0, alert_threshold: float = 0.8):
        self.budget_limit = budget_limit
        self.alert_threshold = alert_threshold
        self.records: list = []
        self.total_cost = 0.0
        self._alerted = False

    def record_call(self, provider: str, model: str, input_tokens: int,
                    output_tokens: int, cost_usd: float):
        """Record a single API call's cost."""
        import datetime
        record = CostRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            timestamp=datetime.datetime.now().isoformat(),
        )
        self.records.append(record)
        self.total_cost += cost_usd

        # Check budget
        if not self._alerted and self.is_near_budget():
            logger.warning("[CostTracker] Budget alert: $%.2f / $%.2f",
                         self.total_cost, self.budget_limit)
            self._alerted = True

    def is_near_budget(self) -> bool:
        """Check if spending is near the alert threshold."""
        return self.total_cost >= (self.budget_limit * self.alert_threshold)

    def is_over_budget(self) -> bool:
        """Check if budget is exceeded."""
        return self.total_cost >= self.budget_limit

    def get_summary(self) -> Dict:
        """Get cost summary."""
        by_provider = {}
        for r in self.records:
            by_provider[r.provider] = by_provider.get(r.provider, 0) + r.cost_usd

        return {
            "total_cost_usd": round(self.total_cost, 4),
            "budget_limit_usd": self.budget_limit,
            "remaining_usd": round(self.budget_limit - self.total_cost, 4),
            "utilization": round(self.total_cost / self.budget_limit, 4) if self.budget_limit > 0 else 0,
            "total_calls": len(self.records),
            "by_provider": {k: round(v, 4) for k, v in by_provider.items()},
        }

    def __repr__(self):
        return f"<CostTracker ${self.total_cost:.2f} / ${self.budget_limit:.2f}>"
