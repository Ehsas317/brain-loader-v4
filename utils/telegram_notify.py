"""
Telegram notifier for Brain Loader v4.

Sends notifications with cost info when tasks complete.
Uses the Telegram Bot API directly via HTTP (no async event loop issues).
"""
from __future__ import annotations
import logging

import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Simple Telegram notifier using the Bot API HTTP endpoint."""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{token}"

    def send(self, message: str) -> None:
        """Send a message to the configured Telegram chat (sync, event-loop safe)."""
        try:
            url = f"{self._base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            logger.info("[Telegram] Notification sent.")
        except Exception as e:
            logger.warning("[Telegram] Failed to send: %s", e)

    def send_sync(self, message: str) -> None:
        """Synchronous wrapper for sending notifications."""
        self.send(message)
