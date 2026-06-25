#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/wave_engine.py                                     ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Wave Engine — the core of Surge. Dispatches tasks in parallel waves
#   across multiple LLM backends for maximum throughput.
#
# HOW TO USE SURGE:
#   1. Install:    pip install -r requirements.txt
#   2. Configure:  Edit config.yaml with your API tokens
#   3. Run:        python main.py "Your project description"
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Wave Engine

Parallel task dispatch across multiple LLM backends.
"""

import asyncio
import logging
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.router import ModelRouter
from core.cost_tracker import CostTracker

logger = logging.getLogger("surge.wave")


class WaveEngine:
    """
    Surge Wave Engine

    Dispatches tasks in parallel waves across multiple LLM backends.
    Each wave sends tasks to all available providers simultaneously,
    returning the best results.

    Usage:
        engine = WaveEngine(router=router, config=config)
        engine.run("Build a fitness app")
    """

    def __init__(self, router: ModelRouter, config: Dict[str, Any]):
        self.router = router
        self.config = config
        self.wave_config = config.get("wave", {})
        self.max_concurrent = self.wave_config.get("max_concurrent", 4)
        self.timeout = self.wave_config.get("timeout_seconds", 120)
        self.cost_tracker = CostTracker(
            budget_limit=config.get("cost_tracking", {}).get("budget_limit", 10.0)
        )

    def run(self, app_idea: str):
        """Main entry point — dispatch waves of tasks."""
        logger.info("[WaveEngine] Starting Surge: %s", app_idea)

        # Phase 1: Planning wave
        plan = self._planning_wave(app_idea)
        tasks = self._decompose_plan(plan)

        # Phase 2: Execution waves
        results = self._execution_waves(tasks)

        # Phase 3: Integration
        self._integrate_results(results)

        logger.info("[WaveEngine] Surge complete!")

    def _planning_wave(self, app_idea: str) -> str:
        """Send planning request to all providers simultaneously."""
        logger.info("[WaveEngine] Planning wave...")

        prompt = f"Create a development plan for: {app_idea}"
        responses = self._dispatch_wave([{"type": "planning", "prompt": prompt}])

        # Use the longest/most detailed plan
        best = max(responses, key=lambda r: len(r.get("content", "")))
        return best.get("content", "")

    def _decompose_plan(self, plan: str) -> List[Dict]:
        """Break plan into parallelizable tasks."""
        import re
        tasks = []
        for match in re.finditer(r'Task\s+(\w+):\s*\((\w+)\)\s*(.+?)(?=Task|$)', plan, re.DOTALL):
            tid, ttype, desc = match.groups()
            tasks.append({"id": tid.strip(), "type": ttype.strip(), "description": desc.strip()})
        return tasks

    def _execution_waves(self, tasks: List[Dict]) -> List[Dict]:
        """Execute tasks in parallel waves."""
        logger.info("[WaveEngine] Executing %d tasks in waves...", len(tasks))
        results = []

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {}
            for task in tasks:
                prompt = self._build_prompt(task)
                future = executor.submit(self._dispatch_task, task, prompt)
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result(timeout=self.timeout)
                    results.append({"task": task, "result": result})
                    logger.info("[WaveEngine] Task %s complete", task.get("id"))
                except Exception as e:
                    logger.error("[WaveEngine] Task %s failed: %s", task.get("id"), e)
                    results.append({"task": task, "error": str(e)})

        return results

    def _dispatch_task(self, task: Dict, prompt: str) -> str:
        """Dispatch a single task to the best available provider."""
        provider_name = self.router.route(task["type"])
        if not provider_name and self.router.providers:
            provider_name = list(self.router.providers.keys())[0]
        return self.router.generate(provider_name, prompt)

    def _dispatch_wave(self, items: List[Dict]) -> List[Dict]:
        """Dispatch multiple items to all providers in parallel."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {}
            for item in items:
                for provider_name in self.router.providers:
                    future = executor.submit(
                        self.router.generate, provider_name, item["prompt"]
                    )
                    futures[future] = provider_name

            for future in as_completed(futures):
                try:
                    content = future.result(timeout=self.timeout)
                    results.append({"provider": futures[future], "content": content})
                except Exception as e:
                    logger.warning("Wave dispatch failed: %s", e)

        return results

    def _build_prompt(self, task: Dict) -> str:
        """Build a prompt for a task."""
        return f"Task: {task.get('description', '')}\n\nProvide complete implementation:"

    def _integrate_results(self, results: List[Dict]):
        """Integrate all task results into final output."""
        logger.info("[WaveEngine] Integrating %d results", len(results))
        for r in results:
            task_id = r["task"].get("id", "unknown")
            if "result" in r:
                logger.info("  %s: OK (%d chars)", task_id, len(r["result"]))
            else:
                logger.warning("  %s: FAILED", task_id)
