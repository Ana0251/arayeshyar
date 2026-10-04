"""
SMS.ir Backend.

─── استفاده: ───
SMS_BACKEND=apps.notifications.backends.smsir.SmsIrBackend
SMSIR_API_KEY=your-api-key
SMSIR_LINE_NUMBER=500039431412769
SMSIR_TEMPLATE_ID=366012
"""

import logging
import re

import requests
from django.conf import settings

from .base import SMSBackend, SMSBackendConfigError, SMSBackendSendError

logger = logging.getLogger(__name__)


class SmsIrBackend(SMSBackend):
    """ارسال SMS با SMS.ir."""

    name = "smsir"
    API_BASE = "https://api.sms.ir/v1"
    TIMEOUT = 15

    def __init__(self):
        self.api_key = getattr(settings, "SMSIR_API_KEY", "")
        self.line_number = getattr(settings, "SMSIR_LINE_NUMBER", "")
        self.template_id = getattr(settings, "SMSIR_TEMPLATE_ID", 0)

        if not self.api_key:
            raise SMSBackendConfigError("SMSIR_API_KEY تنظیم نشده.")

    def send(self, phone, message, *, sms_type="other"):
        """ارسال پیامک با Bulk API."""
        return self._send_bulk(phone, message)

    def _send_bulk(self, phone, message):
        """ارسال پیامک معمولی."""
        url = f"{self.API_BASE}/send/bulk"
        payload = {
            "lineNumber": self.line_number,
            "messageText": message,
            "mobiles": [phone],
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != 1:
                error_msg = data.get("message", "خطای نامشخص")
                logger.error(f"SMS.ir Bulk error: {error_msg}")
                raise SMSBackendSendError(f"SMS.ir: {error_msg}")

            external_id = str(data.get("data", {}).get("messageId", ""))
            logger.info(f"SMS.ir Bulk sent to {phone}: {external_id}")
            return True, external_id

        except requests.RequestException as exc:
            logger.exception(f"SMS.ir Bulk request failed: {exc}")
            raise SMSBackendSendError(f"خطای شبکه: {exc}") from exc