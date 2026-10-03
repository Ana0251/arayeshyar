"""
ثابت‌های notifications.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════════
#  وضعیت ارسال
# ═══════════════════════════════════════════════════════════════


class SMSStatus(models.TextChoices):
    """وضعیت ارسال SMS."""

    PENDING = "pending", _("در انتظار")
    SENT = "sent", _("ارسال شده")
    FAILED = "failed", _("ناموفق")
    DELIVERED = "delivered", _("تحویل داده شده")


# ═══════════════════════════════════════════════════════════════
#  نوع SMS
# ═══════════════════════════════════════════════════════════════


class SMSType(models.TextChoices):
    """نوع پیام."""

    OTP = "otp", _("کد ورود")
    BOOKING_CONFIRM = "booking_confirm", _("تأیید نوبت")
    BOOKING_CANCEL = "booking_cancel", _("لغو نوبت")
    BOOKING_REMINDER = "booking_reminder", _("یادآور نوبت")
    WAITING_LIST = "waiting_list", _("لیست انتظار")
    WELCOME = "welcome", _("خوش‌آمد")
    OTHER = "other", _("سایر")


# ═══════════════════════════════════════════════════════════════
#  محدودیت‌ها
# ═══════════════════════════════════════════════════════════════

# ─── حداکثر طول پیامک ───
MAX_SMS_LENGTH = 160  # کاراکتر

# ─── retry ───
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 60