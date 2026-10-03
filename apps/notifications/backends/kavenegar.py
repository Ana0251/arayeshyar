"""
Kavenegar SMS backend — برای production.

─── مستندات: ───
https://kavenegar.com/rest.html
"""

import logging

import requests
from django.conf import settings

from .base import SMSBackend, SMSBackendConfigError, SMSBackendSendError

logger = logging.getLogger(__name__)


class KavenegarSMSBackend(SMSBackend):
    """
    ارسال SMS با کاوه‌نگار.

    ─── نیازمندی‌ها: ───
    - KAVENEGAR_API_KEY توی .env
    - KAVENEGAR_SENDER (شماره فرستنده)
    """

    name = "kavenegar"

    API_BASE = "https://api.kavenegar.com/v1"
    TIMEOUT = 10  # ثانیه

    def __init__(self) -> None:
        self.api_key = getattr(settings, "KAVENEGAR_API_KEY", "")
        self.sender = getattr(settings, "KAVENEGAR_SENDER", "")

        if not self.api_key:
            raise SMSBackendConfigError(
                "KAVENEGAR_API_KEY توی تنظیمات تنظیم نشده."
            )

    def send(
        self,
        phone: str,
        message: str,
        *,
        sms_type: str = "other",
    ) -> tuple[bool, str]:
        """
        ارسال پیام با کاوه‌نگار.

        ─── API: ───
        GET https://api.kavenegar.com/v1/{API_KEY}/sms/send.json
            ?receptor={phone}&sender={sender}&message={message}
        """
        url = f"{self.API_BASE}/{self.api_key}/sms/send.json"

        params = {
            "receptor": phone,
            "message": message,
        }
        if self.sender:
            params["sender"] = self.sender

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            # ─── چک پاسخ ───
            if data.get("return", {}).get("status") != 200:
                error_msg = data.get("return", {}).get("message", "خطای نامشخص")
                logger.error(f"Kavenegar error: {error_msg}")
                raise SMSBackendSendError(f"کاوه‌نگار: {error_msg}")

            # ─── استخراج message_id ───
            entries = data.get("entries", [])
            if not entries:
                raise SMSBackendSendError("پاسخ کاوه‌نگار خالی بود.")

            external_id = str(entries[0].get("messageid", ""))
            logger.info(f"Kavenegar SMS sent to {phone}: {external_id}")

            return True, external_id

        except requests.RequestException as exc:
            logger.exception(f"Kavenegar request failed: {exc}")
            raise SMSBackendSendError(f"خطای شبکه: {exc}") from exc