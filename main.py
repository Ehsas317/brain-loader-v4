#!/usr/bin/env python3
"""
Brain Loader v4 — Entry Point

Usage:
    python main.py                           # Interactive REPL
    python main.py "Build a FastAPI server"  # Headless (no approval prompts)
    python main.py --config path/to/config.yaml
"""

import asyncio
import logging
import sys
from pathlib import Path

import yaml


def load_config(path: str = "config.yaml") -> dict:
    config_path = Path(path)
    if not config_path.exists():
        print(f"[ERROR] Config not found: {path}")
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def setup_logging() -> None:
    Path("./logs").mkdir(exist_ok=True)
    from datetime import datetime
    log_file = f"./logs/v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)-24s %(levelname)-8s %(message)s",
        handlers=[logging.FileHandler(log_file)],
        # No StreamHandler — rich console handles all display
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def _main() -> None:
    # Parse minimal CLI
    config_path = "config.yaml"
    goal_parts = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--config" and i + 1 < len(args):
            config_path = args[i + 1]
            i += 2
        else:
            goal_parts.append(args[i])
            i += 1

    setup_logging()
    config = load_config(config_path)

    # Import here so logging is set up first
    from core.router import UniversalRouter
    from core.wave_engine import WaveEngine
    from tui.repl import BrainREPL

    router = UniversalRouter(config)
    wave_engine = WaveEngine(router, config)
    repl = BrainREPL(config, router, wave_engine)

    if goal_parts:
        # Headless: skip approval prompt
        goal = " ".join(goal_parts)
        await repl._run_goal(goal, auto_approve=True)
    else:
        # Interactive REPL
        await repl.start()


if __name__ == "__main__":
    asyncio.run(_main())
