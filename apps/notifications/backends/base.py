"""
Base SMS backend.
"""

from abc import ABC, abstractmethod


# ═══════════════════════════════════════════════════════════════
#  Exceptions
# ═══════════════════════════════════════════════════════════════


class SMSBackendError(Exception):
    """خطای عمومی backend."""


class SMSBackendConfigError(SMSBackendError):
    """تنظیمات ناقص."""


class SMSBackendSendError(SMSBackendError):
    """خطا در ارسال."""


# ═══════════════════════════════════════════════════════════════
#  Base
# ═══════════════════════════════════════════════════════════════


class SMSBackend(ABC):
    """
    کلاس پایه برای همه‌ی SMS backend ها.

    ─── قرارداد: ───
    - send(phone, message, sms_type) → (success, external_id)
    - اگه خطا بده، SMSBackendSendError raise می‌کنه
    """

    name: str = "base"

    @abstractmethod
    def send(
        self,
        phone: str,
        message: str,
        *,
        sms_type: str = "other",
    ) -> tuple[bool, str]:
        """
        ارسال SMS.

        Args:
            phone: شماره موبایل
            message: متن پیام
            sms_type: نوع پیام (برای rate limiting)

        Returns:
            (success: bool, external_id: str)
        """
        ...