#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: tui/__init__.py                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   TUI package initializer for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — TUI Package

Terminal User Interface for interactive Surge control.
"""

from tui.repl import SurgeREPL

__all__ = ["SurgeREPL"]
