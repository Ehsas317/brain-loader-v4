#!/usr/bin/env python3
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SURGE  — FILE: utils/telegram_notify.py                                ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# PROJECT:    Surge (formerly Brain Loader v4)
# REPO:       https://github.com/Ehsas317/surge
# WHAT:       Wave-based parallel dispatch across multiple backends.
#             A surge is simultaneous and forceful.
#
# THIS FILE:
#   Telegram Notifier — real-time build progress updates for Surge.
#
# ═══════════════════════════════════════════════════════════════════════════
#

"""
Surge — Telegram Notifier

Sends real-time build progress updates via Telegram.
"""

import logging
import httpx

logger = logging.getLogger("surge.telegram")


class TelegramNotifier:
    """
    Surge Telegram Notifier

    Usage:
        notifier = TelegramNotifier(bot_token="...", chat_id="...")
        notifier.send("⚡ Surge starting...")
    """

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._enabled = bool(bot_token and chat_id)

    def send(self, message: str) -> bool:
        if not self._enabled:
            return False
        try:
            payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
            resp = httpx.post(f"{self.base_url}/sendMessage", json=payload, timeout=10.0)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            return False

    def send_file(self, file_path: str, caption: str = "") -> bool:
        if not self._enabled:
            return False
        try:
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": self.chat_id, "caption": caption}
                resp = httpx.post(f"{self.base_url}/sendDocument", data=data, files=files, timeout=30.0)
                resp.raise_for_status()
            return True
        except Exception as e:
            logger.error("Telegram file send failed: %s", e)
            return False
