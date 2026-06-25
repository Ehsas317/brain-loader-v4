#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: core/__init__.py                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Core package initializer for Surge. Exports main classes.
#
# HOW TO USE SURGE:
#   1. Install:    pip install -r requirements.txt
#   2. Configure:  Edit config.yaml with your API tokens
#   3. Run:        python main.py "Your project description"
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Core Package

Exposes the main orchestration classes:
- WaveEngine: Parallel task dispatch
- ModelRouter: Multi-backend routing
- CostTracker: Cost monitoring
"""

from core.wave_engine import WaveEngine
from core.router import ModelRouter
from core.cost_tracker import CostTracker

__all__ = ["WaveEngine", "ModelRouter", "CostTracker"]
