#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: utils/state_manager.py                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   State Manager — persistent JSON state with resume support for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — State Manager

Persistent JSON state management with resume support.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("surge.state")


class StateManager:
    """
    Surge State Manager

    Manages persistent application state in JSON format.

    Usage:
        state_mgr = StateManager()
        state_mgr.save_project_state({...})
        state = state_mgr.load_project_state()
    """

    def __init__(self, state_file: str = "memory/state.json"):
        self.state_file = Path(state_file)

    def save_project_state(self, state: Dict[str, Any]):
        """Save project state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        logger.debug("[StateManager] State saved")

    def load_project_state(self) -> Dict[str, Any]:
        """Load project state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("[StateManager] Failed to load state: %s", e)
        return {}

    def reset(self):
        """Reset state for a new project."""
        if self.state_file.exists():
            self.state_file.unlink()
        logger.info("[StateManager] State reset")
