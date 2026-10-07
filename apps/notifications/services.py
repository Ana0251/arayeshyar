"""
سرویس‌های notifications.

منطق اصلی ارسال SMS + لاگ.
"""

import logging

from django.utils import timezone

from apps.core.utils.dates import to_jalali_date

from .backends import (
    SMSBackendError,
    get_sms_backend,
)
from .constants import SMSStatus, SMSType
from .models import SMSLog

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Send SMS
# ═══════════════════════════════════════════════════════════════


def send_sms(
    phone: str,
    message: str,
    *,
    sms_type: str = SMSType.OTHER,
) -> SMSLog:
    """
    ارسال SMS + لاگ.

    Args:
        phone: شماره موبایل
        message: متن پیام
        sms_type: نوع پیام

    Returns:
        SMSLog

    Raises:
        SMSBackendError
    """
    # ─── نرمال‌سازی ───
    from apps.core.utils.phone import normalize_phone

    normalized = normalize_phone(phone)
    if not normalized:
        raise ValueError(f"شماره نامعتبر: {phone}")

    # ─── ساخت لاگ ───
    log = SMSLog.objects.create(
        phone=normalized,
        message=message,
        sms_type=sms_type,
        status=SMSStatus.PENDING,
    )

    # ─── ارسال ───
    try:
        backend = get_sms_backend()
        log.backend = backend.name
        log.save(update_fields=["backend"])

        success, external_id = backend.send(
            normalized,
            message,
            sms_type=sms_type,
        )

        if success:
            log.mark_sent(external_id=external_id)
            logger.info(f"SMS sent to {normalized} via {backend.name}")
        else:
            log.mark_failed(error="ارسال ناموفق")
            logger.warning(f"SMS failed to {normalized}")

    except SMSBackendError as exc:
        log.mark_failed(error=str(exc))
        logger.exception(f"SMS backend error: {exc}")
        raise

    except Exception as exc:
        log.mark_failed(error=f"خطای غیرمنتظره: {exc}")
        logger.exception(f"Unexpected SMS error: {exc}")
        raise

    return log


def _jalali_if_date(value) -> str:
    """اگر date/datetime داده شد شمسی کن؛ رشته را دست‌نخورده برگردان."""
    from datetime import date, datetime
    if isinstance(value, (date, datetime)):
        return to_jalali_date(value)
    return str(value)


# ═══════════════════════════════════════════════════════════════
#  Templates — پیام‌های آماده
# ═══════════════════════════════════════════════════════════════


def send_otp_sms(phone: str, code: str, expiry_minutes: int = 2) -> SMSLog:
    """ارسال کد OTP."""
    message = (
        f"کد ورود شما به آرایشیار:\n"
        f"{code}\n"
        f"اعتبار: {expiry_minutes} دقیقه"
    )
    return send_sms(phone, message, sms_type=SMSType.OTP)


def send_booking_confirmed_sms(
    phone: str,
    business_name: str,
    date_str: str,
    time_str: str,
) -> SMSLog:
    """تأیید نوبت."""
    message = (
        f"✅ نوبت شما تأیید شد.\n"
        f"📍 {business_name}\n"
        f"📅 {_jalali_if_date(date_str)} ساعت {time_str}\n"
        f"آرایشیار"
    )
    return send_sms(phone, message, sms_type=SMSType.BOOKING_CONFIRM)


def send_booking_cancelled_sms(
    phone: str,
    business_name: str,
    date_str: str,
    time_str: str,
) -> SMSLog:
    """لغو نوبت."""
    message = (
        f"❌ نوبت شما لغو شد.\n"
        f"📍 {business_name}\n"
        f"📅 {_jalali_if_date(date_str)} ساعت {time_str}\n"
        f"آرایشیار"
    )
    return send_sms(phone, message, sms_type=SMSType.BOOKING_CANCEL)


def send_booking_reminder_sms(
    phone: str,
    business_name: str,
    time_str: str,
) -> SMSLog:
    """یادآور نوبت."""
    message = (
        f"⏰ یادآوری نوبت\n"
        f"📍 {business_name}\n"
        f"🕐 امروز ساعت {time_str}\n"
        f"آرایشیار"
    )
    return send_sms(phone, message, sms_type=SMSType.BOOKING_REMINDER)


def send_waiting_list_sms(
    phone: str,
    business_name: str,
    date_str: str,
) -> SMSLog:
    """اطلاع آزاد شدن ساعت."""
    message = (
        f"🎉 یه ساعت توی {business_name} آزاد شد!\n"
        f"📅 {_jalali_if_date(date_str)}\n"
        f"برای رزرو سریع وارد شو.\n"
        f"آرایشیار"
    )
    return send_sms(phone, message, sms_type=SMSType.WAITING_LIST)


# ═══════════════════════════════════════════════════════════════
#  Retro-compat (از accounts.services صداش می‌زنیم)
# ═══════════════════════════════════════════════════════════════

# توی accounts/services.py، send_sms(phone, message) صدا زده میشه.
# این تابع همون امضاست. ✅