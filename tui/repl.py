#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: tui/repl.py                                             ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   TUI REPL — interactive terminal interface for Surge. Provides a
#   command-line interface to monitor and control parallel dispatch.
#
# HOW TO USE SURGE:
#   1. Install:    pip install -r requirements.txt
#   2. Configure:  Edit config.yaml with your API tokens
#   3. Run:        python main.py "Your project description"
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — TUI REPL

Interactive terminal interface for monitoring and controlling Surge.
"""

import os
import sys
import cmd
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("surge.tui")


class SurgeREPL(cmd.Cmd):
    """
    Surge Interactive TUI

    Provides a command-line interface to:
    - Start and monitor builds
    - View task status and provider health
    - Check cost tracking
    - Export results

    Usage:
        repl = SurgeREPL(engine)
        repl.cmdloop()
    """

    intro = """
    ⚡ Surge — Wave-Based Parallel Dispatch
    Type 'help' for commands, 'start' to begin, 'quit' to exit.
    """
    prompt = "surge> "

    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        self.current_project = None

    def do_start(self, arg):
        """Start a new build. Usage: start <project description>"""
        if not arg:
            print("Usage: start <project description>")
            return
        self.current_project = arg
        print(f"\n⚡ Starting: {arg}")
        if self.engine:
            try:
                self.engine.run(arg)
                print("\n✅ Build complete!")
            except Exception as e:
                print(f"\n❌ Build failed: {e}")
        else:
            print("Engine not initialized. Run from main.py.")

    def do_status(self, arg):
        """Show current build status."""
        if not self.current_project:
            print("No active project. Use 'start' to begin.")
            return
        print(f"\n📊 Project: {self.current_project}")
        if self.engine:
            summary = self.engine.cost_tracker.get_summary()
            print(f"  Cost: ${summary['total_cost_usd']} / ${summary['budget_limit_usd']}")
            print(f"  Calls: {summary['total_calls']}")
            print(f"  By Provider: {summary['by_provider']}")

    def do_providers(self, arg):
        """List all configured providers and their health status."""
        if not self.engine:
            print("Engine not initialized.")
            return
        print("\n🔌 Providers:")
        for name, cfg in self.engine.router.providers.items():
            health = "✅" if self.engine.router.providers[name] else "❌"
            print(f"  {health} {name}: {cfg.get('model', 'N/A')}")

    def do_cost(self, arg):
        """Show cost summary."""
        if not self.engine:
            print("Engine not initialized.")
            return
        summary = self.engine.cost_tracker.get_summary()
        print(f"\n💰 Cost Summary:")
        print(f"  Total: ${summary['total_cost_usd']}")
        print(f"  Budget: ${summary['budget_limit_usd']}")
        print(f"  Remaining: ${summary['remaining_usd']}")
        print(f"  Utilization: {summary['utilization'] * 100:.1f}%")

    def do_quit(self, arg):
        """Exit Surge TUI."""
        print("\n👋 Goodbye!")
        return True

    def do_EOF(self, arg):
        """Handle Ctrl+D."""
        return self.do_quit(arg)

    def emptyline(self):
        """Do nothing on empty line."""
        pass
