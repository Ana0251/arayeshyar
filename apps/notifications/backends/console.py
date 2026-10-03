"""
Console SMS backend — برای development.

پیام‌ها رو توی terminal چاپ می‌کنه.
"""

import logging

from .base import SMSBackend

logger = logging.getLogger(__name__)


class ConsoleSMSBackend(SMSBackend):
    """
    چاپ پیام‌ها توی console.

    ─── استفاده: ───
    توی `settings.py`:
        SMS_BACKEND = "apps.notifications.backends.console.ConsoleSMSBackend"
    """

    name = "console"

    def send(
        self,
        phone: str,
        message: str,
        *,
        sms_type: str = "other",
    ) -> tuple[bool, str]:
        """چاپ پیام."""
        print("\n" + "═" * 60)
        print(f"📱 SMS [{sms_type}]")
        print(f"   به: {phone}")
        print(f"   متن: {message}")
        print("═" * 60 + "\n")

        logger.info(f"Console SMS to {phone}: {message}")

        return True, f"console-{phone}"