#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: main.py                                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Entry point for the Surge multi-backend parallel orchestrator.
#   Dispatches tasks across multiple LLM backends simultaneously.
#
# HOW TO USE SURGE:
#   1. Install:    pip install -r requirements.txt
#   2. Configure:  Edit config.yaml with your API tokens
#   3. Run:        python main.py "Your project description"
#
# HARDWARE TARGET: MacBook Pro M1 Max 32GB (25GB allocated)
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Main Entry Point

Usage:
    python main.py "Build a React Native fitness app"
    python main.py --resume
    python main.py --config custom_config.yaml

Hardware: MacBook Pro M1 Max 32GB (25GB allocated)
"""

import os
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.wave_engine import WaveEngine
from core.router import ModelRouter
from utils.telegram_notify import TelegramNotifier


def setup_logging(logs_dir: str = "./logs"):
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(logs_dir) / f"surge_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return log_file


def main():
    parser = argparse.ArgumentParser(description="Surge — Wave-Based Parallel Dispatch")
    parser.add_argument("idea", nargs="?", help="Project description")
    parser.add_argument("--resume", action="store_true", help="Resume project")
    parser.add_argument("--config", default="config.yaml", help="Config file")
    parser.add_argument("--list-models", action="store_true", help="List models")
    args = parser.parse_args()

    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("SURGE — Wave-Based Parallel Dispatch")
    logger.info("Hardware: MacBook Pro M1 Max 32GB (25GB allocated)")
    logger.info("=" * 70)

    if not Path(args.config).exists():
        logger.error("Config not found: %s", args.config)
        sys.exit(1)

    import yaml
    with open(args.config) as f:
        config = yaml.safe_load(f)

    router = ModelRouter(config.get("providers", {}))
    engine = WaveEngine(router=router, config=config)

    if args.list_models:
        print("\nAvailable Providers:")
        for name, provider in router.providers.items():
            print(f"  {name}: {provider}")
        sys.exit(0)

    if args.idea:
        logger.info("Starting: %s", args.idea)
        engine.run(args.idea)
    else:
        print("\n⚡ Surge — Parallel Dispatch")
        idea = input("> ").strip()
        if idea:
            engine.run(idea)

    logger.info("Surge complete. Log: %s", log_file)
    print(f"\n✅ Done! Log: {log_file}")


if __name__ == "__main__":
    main()
