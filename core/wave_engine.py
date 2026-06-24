"""Wave Engine — Brain planning, parallel task dispatch, synthesis."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from .router import UniversalRouter, RouteResult

logger = logging.getLogger(__name__)

_PLAN_SYSTEM = """\
You are the Brain — the strategic planner in the Brain Loader v4 system.

Your job: decompose the user's goal into a wave of parallel specialist tasks.

OUTPUT FORMAT: Valid JSON only. No prose. No markdown code fences. Exactly this schema:

{
  "goal_understood": "one-sentence restatement of the goal",
  "tasks": [
    {
      "id": "T1",
      "role": "researcher",
      "prompt": "detailed prompt for the specialist — be specific",
      "parallel_safe": true
    }
  ],
  "synthesis_notes": "how to combine task outputs into a final answer",
  "wave_count_estimate": 1
}

Rules:
- parallel_safe: true  → task can run alongside other tasks
- parallel_safe: false → task needs results from parallel tasks first (runs after them)
- Aim for 2–5 tasks per wave. More tasks = more parallelism = faster results.
- Available roles: researcher, coder, writer, math, critic
- One role per task. Prompts must be self-contained and detailed.
"""

_SYNTHESIS_SYSTEM = """\
You are the Brain synthesizing your specialist team's outputs into a final answer.

Write a complete, well-structured markdown response that:
1. Directly answers the original goal
2. Incorporates all relevant findings from each specialist
3. Notes any conflicting information or failed tasks
4. Is thorough — this is the deliverable the user will read

Do not add meta-commentary about the process. Just write the answer.
"""


@dataclass
class Task:
    id: str
    role: str
    prompt: str
    parallel_safe: bool = True


class WaveEngine:
    def __init__(self, router: UniversalRouter, config: dict):
        self.router = router
        self.config = config

    async def plan(
        self, goal: str, memory_context: str = ""
    ) -> tuple[str, List[Task], str]:
        ctx = f"\n\n## Session Context (recent history)\n{memory_context}" if memory_context else ""
        prompt = f"Plan the following goal:{ctx}\n\n## Goal\n{goal}"

        result = await self.router.execute(
            role="brain", task_id="brain_plan", prompt=prompt, system=_PLAN_SYSTEM
        )

        if not result.success:
            raise RuntimeError(f"Brain planning failed: {result.error}")

        text = result.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                raise RuntimeError(f"Brain did not return valid JSON:\n{text[:600]}")
            data = json.loads(m.group())

        tasks = [
            Task(
                id=t["id"],
                role=t.get("role", "researcher"),
                prompt=t["prompt"],
                parallel_safe=t.get("parallel_safe", True),
            )
            for t in data.get("tasks", [])
        ]

        return (
            data.get("goal_understood", goal),
            tasks,
            data.get("synthesis_notes", ""),
        )

    async def dispatch(
        self,
        tasks: List[Task],
        result_queue: Optional[asyncio.Queue] = None,
    ) -> List[RouteResult]:
        parallel = [t for t in tasks if t.parallel_safe]
        sequential = [t for t in tasks if not t.parallel_safe]

        all_results: List[RouteResult] = []

        if parallel:
            logger.info("[Wave] Dispatching %d parallel task(s)", len(parallel))
            coros = [
                self.router.execute(role=t.role, task_id=t.id, prompt=t.prompt)
                for t in parallel
            ]
            for coro in asyncio.as_completed(coros):
                r = await coro
                all_results.append(r)
                if result_queue:
                    await result_queue.put(r)

        for task in sequential:
            context_block = "\n\n".join(
                f"### {r.task_id} [{r.role}]\n{r.text[:2500]}"
                for r in all_results if r.success
            )
            aug_prompt = task.prompt
            if context_block:
                aug_prompt += f"\n\n## Results from parallel tasks\n{context_block}"

            r = await self.router.execute(role=task.role, task_id=task.id, prompt=aug_prompt)
            all_results.append(r)
            if result_queue:
                await result_queue.put(r)

        return all_results

    async def synthesize(
        self,
        goal: str,
        results: List[RouteResult],
        synthesis_notes: str = "",
    ) -> str:
        sections = []
        for r in results:
            status = "✓ Complete" if r.success else "✗ FAILED"
            body = r.text if r.success else f"Error: {r.error}"
            sections.append(
                f"### Task {r.task_id} [{r.role}] — {status}\n"
                f"_Provider: {r.provider} / {r.model.split('/')[-1]}_\n\n{body}"
            )

        prompt = (
            f"## Original Goal\n{goal}\n\n"
            f"## Synthesis Notes\n{synthesis_notes or 'Combine all outputs coherently.'}\n\n"
            f"## Specialist Outputs\n\n"
            + "\n\n---\n\n".join(sections)
        )

        result = await self.router.execute(
            role="brain", task_id="synthesis", prompt=prompt, system=_SYNTHESIS_SYSTEM
        )

        return result.text if result.success else "Synthesis failed — check logs."
