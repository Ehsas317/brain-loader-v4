"""
Brain Loader v4 — Terminal REPL

Powered by Rich. Shows live wave status table as tasks complete.
Supports HITL (Human-in-the-Loop) approval before each wave.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich import box
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.spinner import Spinner
from rich.table import Table

from core.router import RouteResult, UniversalRouter
from core.wave_engine import Task, WaveEngine

logger = logging.getLogger(__name__)

_HELP = """\
[bold cyan]Commands[/bold cyan]
  /status   Provider health + session token stats
  /memory   Show current memory.md
  /mode     Current mode (local / api / hybrid)
  /cost     Current session cost
  /save     Save last output to file manually
  /exit     Quit
"""


class BrainREPL:
    def __init__(self, config: dict, router: UniversalRouter, wave_engine: WaveEngine):
        self.config = config
        self.router = router
        self.wave_engine = wave_engine
        self.console = Console()
        self.mode = config.get("mode", "hybrid").upper()
        self.outputs_dir = Path(config["project"]["outputs_dir"])
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = Path(config["project"]["memory_file"])
        self.memory_ctx_bytes: int = config["project"].get("memory_context_bytes", 3000)
        self._last_output: Optional[str] = None

    async def start(self) -> None:
        """Interactive REPL loop."""
        self._banner()
        while True:
            try:
                user_in = Prompt.ask("\n[bold green]You[/bold green]", console=self.console)
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Use /exit to quit.[/dim]")
                continue

            if not user_in.strip():
                continue
            if user_in.startswith("/"):
                keep_going = await self._command(user_in.strip())
                if not keep_going:
                    break
                continue
            await self._run_goal(user_in.strip())

    async def _run_goal(self, goal: str, auto_approve: bool = False) -> None:
        """Full agentic cycle: plan → approve → dispatch → synthesize."""

        # 1. Brain plans
        self.console.print()
        goal_understood, tasks, synthesis_notes = await self._brain_plan(goal)

        if not tasks:
            self.console.print("[red]Brain returned no tasks. Try rephrasing your goal.[/red]")
            return

        # 2. Show plan table
        self._print_plan(tasks, goal_understood)

        # 3. HITL approval (skip in headless/auto mode)
        if not auto_approve:
            if not Confirm.ask("\n[bold yellow]Approve this wave?[/bold yellow]", console=self.console):
                self.console.print("[dim]Wave aborted by user.[/dim]")
                return

        # 4. Dispatch wave with live status
        self.console.print(
            f"\n[bold cyan]🌊 Dispatching {len(tasks)} task(s) in {self.mode} mode...[/bold cyan]\n"
        )
        results = await self._dispatch_live(tasks)

        # 5. Synthesize
        synthesis = await self._synthesize(goal, results, synthesis_notes)

        # 6. Display and save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = self.outputs_dir / f"output_{timestamp}.md"
        out_path.write_text(f"# Goal: {goal}\n\n{synthesis}", encoding="utf-8")
        self._last_output = synthesis

        self.console.print()
        self.console.print(Panel(
            Markdown(synthesis),
            title="[bold green]✓ Final Answer[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
        self.console.print(f"[dim]Saved → {out_path}[/dim]\n")
        self.console.print(f"[dim]{self.router.get_stats()}[/dim]")

        # 7. Update memory
        self._append_memory(goal, synthesis)

        # 8. Telegram (if configured)
        self._notify(f"✅ Brain Loader v4\n*Goal:* {goal[:100]}\n\nSaved: `{out_path}`")

    async def _brain_plan(self, goal: str):
        memory_ctx = ""
        if self.memory_file.exists():
            raw = self.memory_file.read_bytes()
            memory_ctx = raw[-self.memory_ctx_bytes:].decode("utf-8", errors="replace")

        with Live(
            Spinner("dots", text="[bold magenta]Brain is planning your wave...[/bold magenta]"),
            console=self.console,
            refresh_per_second=10,
        ):
            return await self.wave_engine.plan(goal, memory_ctx)

    def _print_plan(self, tasks: List[Task], goal_understood: str) -> None:
        table = Table(
            title=f'Brain\'s Proposed Wave — "{goal_understood[:70]}"',
            box=box.ROUNDED,
            border_style="magenta",
            header_style="bold magenta",
        )
        table.add_column("ID", width=4)
        table.add_column("Role", style="cyan", width=12)
        table.add_column("Prompt preview", width=60)
        table.add_column("Parallel", width=9)

        for t in tasks:
            preview = t.prompt[:65] + "…" if len(t.prompt) > 65 else t.prompt
            parallel_cell = "[green]✓ Yes[/green]" if t.parallel_safe else "[yellow]⏳ After[/yellow]"
            table.add_row(t.id, t.role, preview, parallel_cell)

        self.console.print(table)

    async def _dispatch_live(self, tasks: List[Task]) -> List[RouteResult]:
        statuses = {
            t.id: {
                "role": t.role,
                "status": "[cyan]🔄 Running[/cyan]" if t.parallel_safe else "⏳ Pending",
                "provider": "—",
                "time": "—",
            }
            for t in tasks
        }

        result_q: asyncio.Queue = asyncio.Queue()
        all_results: List[RouteResult] = []
        completed_ids: set = set()

        def make_table() -> Table:
            tbl = Table(box=box.SIMPLE, show_header=True, header_style="bold")
            tbl.add_column("ID", width=4)
            tbl.add_column("Role", width=12)
            tbl.add_column("Status", width=22)
            tbl.add_column("Provider / Model", width=30)
            tbl.add_column("Time", width=7)
            for tid, s in statuses.items():
                tbl.add_row(tid, s["role"], s["status"], s["provider"], s["time"])
            return tbl

        # FIX BUG-V4-004: Wrap dispatch in try/except to handle exceptions
        # and put an error sentinel in the queue so the REPL doesn't hang.
        async def _run_dispatch():
            try:
                await self.wave_engine.dispatch(tasks, result_queue=result_q)
            except Exception as e:
                logger.error("[REPL] Wave dispatch failed: %s", e)
                # Put error result for each incomplete task
                for t in tasks:
                    if t.id not in completed_ids:
                        await result_q.put(RouteResult(
                            task_id=t.id, role=t.role, text="", provider="none", model="none",
                            elapsed_s=0, success=False,
                            error=f"Dispatch failed: {e}",
                        ))
            await result_q.put(None)  # sentinel

        dispatch_task = asyncio.create_task(_run_dispatch())

        with Live(make_table(), console=self.console, refresh_per_second=5) as live:
            while True:
                try:
                    result = await asyncio.wait_for(result_q.get(), timeout=0.3)
                except asyncio.TimeoutError:
                    live.update(make_table())
                    continue

                if result is None:
                    live.update(make_table())
                    break

                completed_ids.add(result.task_id)
                s = statuses.get(result.task_id, {})
                if result.success:
                    short_model = result.model.split("/")[-1][:22]
                    s["status"] = "[green]✓ Done[/green]"
                    s["provider"] = f"{result.provider} / {short_model}"
                    s["time"] = f"{result.elapsed_s:.1f}s"
                else:
                    s["status"] = "[red]✗ Failed[/red]"
                    s["time"] = "—"

                all_results.append(result)

                parallel_ids = {t.id for t in tasks if t.parallel_safe}
                if parallel_ids.issubset(completed_ids):
                    for t in tasks:
                        if not t.parallel_safe and t.id not in completed_ids:
                            statuses[t.id]["status"] = "[cyan]🔄 Running[/cyan]"

                live.update(make_table())

        # FIX BUG-V4-004: Await the dispatch task to catch any exceptions
        try:
            await dispatch_task
        except Exception as e:
            logger.error("[REPL] Dispatch task raised: %s", e)

        for r in all_results:
            if r.success:
                self.console.print(Panel(
                    Markdown(r.text),
                    title=f"[bold]{r.task_id} · {r.role}[/bold]  [dim]({r.provider})[/dim]",
                    border_style="blue",
                    padding=(1, 2),
                ))
            else:
                self.console.print(Panel(
                    f"[red]{r.error}[/red]",
                    title=f"[bold red]✗ {r.task_id} FAILED[/bold red]",
                    border_style="red",
                ))

        return all_results

    async def _synthesize(self, goal: str, results: List[RouteResult], notes: str) -> str:
        with Live(
            Spinner("dots", text="[bold magenta]Brain synthesizing all outputs...[/bold magenta]"),
            console=self.console,
            refresh_per_second=10,
        ):
            return await self.wave_engine.synthesize(goal, results, notes)

    def _append_memory(self, goal: str, synthesis: str) -> None:
        # FIX BUG-V4-006: Ensure parent directory exists before appending
        # (handles case where outputs_dir is deleted mid-run)
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            summary_line = synthesis[:200].replace("\n", " ")
            entry = f"\n### [{timestamp}] Goal: {goal[:80]}\n{summary_line}…\n"
            with open(self.memory_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            logger.warning("[REPL] Failed to append memory: %s", e)

    def _notify(self, message: str) -> None:
        tg = self.config.get("telegram", {})
        if not (tg.get("token") and tg.get("chat_id")):
            return
        try:
            from utils.telegram_notify import TelegramNotifier
            TelegramNotifier(tg["token"], tg["chat_id"]).send(message)
        except Exception as e:
            logger.debug("[Telegram] %s", e)

    async def _command(self, cmd: str) -> bool:
        if cmd == "/exit":
            self.console.print("[dim]Goodbye.[/dim]")
            return False

        elif cmd == "/status":
            tbl = Table(title="Provider Status", box=box.ROUNDED)
            tbl.add_column("Provider", style="cyan")
            tbl.add_column("Available")
            tbl.add_column("Circuit State")
            for name, prov in self.router._providers.items():
                avail = "[green]✓ Yes[/green]" if prov.is_available() else "[red]✗ No[/red]"
                cb_state = self.router.circuit_breakers[name].state if name in self.router.circuit_breakers else "n/a"
                tbl.add_row(name, avail, cb_state)
            self.console.print(tbl)
            self.console.print(f"\n[dim]{self.router.get_stats()}[/dim]")

        elif cmd == "/memory":
            if self.memory_file.exists():
                self.console.print(Panel(
                    Markdown(self.memory_file.read_text()),
                    title="memory.md",
                    border_style="yellow",
                ))
            else:
                self.console.print("[dim]No memory file yet.[/dim]")

        elif cmd == "/mode":
            self.console.print(f"Current mode: [bold green]{self.mode}[/bold green]")

        elif cmd == "/cost":
            cost = self.router.stats.total_cost_usd
            self.console.print(f"Session cost: [bold]${cost:.4f}[/bold]")

        elif cmd == "/save":
            if self._last_output:
                path = self.outputs_dir / f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                path.write_text(self._last_output, encoding="utf-8")
                self.console.print(f"[green]Saved → {path}[/green]")
            else:
                self.console.print("[dim]Nothing to save yet.[/dim]")

        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")

        return True

    def _banner(self) -> None:
        providers_status = []
        for name, prov in self.router._providers.items():
            if prov.is_available():
                providers_status.append(f"[green]{name}[/green]")
            else:
                providers_status.append(f"[dim]{name}[/dim]")

        self.console.print(Panel.fit(
            f"[bold cyan]Brain Loader v4[/bold cyan]  —  Terminal Interactive Edition\n"
            f"Mode: [bold green]{self.mode}[/bold green]\n"
            f"Providers: {' · '.join(providers_status)}\n\n"
            f"{_HELP}",
            border_style="cyan",
            title="[bold]TIE[/bold]",
        ))
