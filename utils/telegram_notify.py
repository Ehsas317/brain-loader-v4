"""
Telegram notifier for Brain Loader v4.

Sends notifications with cost info when tasks complete.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Simple Telegram notifier using python-telegram-bot."""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def send(self, message: str) -> None:
        """Send a message to the configured Telegram chat."""
        try:
            import telegram
            from telegram.constants import ParseMode

            async def _send():
                bot = telegram.Bot(token=self.token)
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                )

            import asyncio
            asyncio.run(_send())
            logger.info("[Telegram] Notification sent.")
        except Exception as e:
            logger.warning("[Telegram] Failed to send: %s", e)

    def send_sync(self, message: str) -> None:
        """Synchronous wrapper for sending notifications."""
        self.send(message)
