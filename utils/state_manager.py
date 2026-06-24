"""
State Manager — Crash recovery for Brain Loader v4.

Saves and restores session state so that long-running tasks
can resume after an unexpected exit.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StateManager:
    """Manages persistent state for crash recovery."""

    def __init__(self, state_file: str = "./state.json"):
        self.state_file = Path(state_file)
        self._state: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load state from disk if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
                logger.info("[StateManager] Loaded state from %s", self.state_file)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("[StateManager] Failed to load state: %s", e)
                self._state = {}
        else:
            self._state = {}

    def save(self) -> None:
        """Save current state to disk."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
            logger.debug("[StateManager] State saved.")
        except IOError as e:
            logger.error("[StateManager] Failed to save state: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in state and persist."""
        self._state[key] = value
        self.save()

    def update(self, data: Dict[str, Any]) -> None:
        """Update multiple values at once."""
        self._state.update(data)
        self.save()

    def clear(self) -> None:
        """Clear all state."""
        self._state = {}
        if self.state_file.exists():
            self.state_file.unlink()
        logger.info("[StateManager] State cleared.")

    @property
    def state(self) -> Dict[str, Any]:
        """Access the full state dictionary."""
        return self._state.copy()
