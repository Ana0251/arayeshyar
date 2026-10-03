"""
Telegram SMS Backend — برای Development.

پیام‌ها را به تلگرام می‌فرستد (جایگزین SMS).
"""

import logging

import requests
from django.conf import settings

from .base import SMSBackend, SMSBackendConfigError, SMSBackendSendError

logger = logging.getLogger(__name__)


class TelegramSMSBackend(SMSBackend):
    """ارسال SMS به تلگرام (برای dev)."""

    name = "telegram"

    def __init__(self) -> None:
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        self.chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")

        if not self.bot_token:
            raise SMSBackendConfigError("TELEGRAM_BOT_TOKEN تنظیم نشده.")
        if not self.chat_id:
            raise SMSBackendConfigError("TELEGRAM_CHAT_ID تنظیم نشده.")

    def send(self, phone: str, message: str, *, sms_type: str = "other") -> tuple[bool, str]:
        """ارسال پیام به تلگرام."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        text = f"📱 به: {phone}\n[{sms_type}]\n\n{message}"

        try:
            response = requests.post(
                url,
                json={"chat_id": self.chat_id, "text": text},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                raise SMSBackendSendError(
                    f"خطای تلگرام: {data.get('description', 'نامشخص')}"
                )

            logger.info(f"Telegram SMS sent for {phone}")
            return True, f"telegram-{data['result']['message_id']}"

        except requests.RequestException as exc:
            logger.exception(f"Telegram send failed: {exc}")
            raise SMSBackendSendError(f"خطای شبکه تلگرام: {exc}") from exc