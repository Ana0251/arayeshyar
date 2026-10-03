"""
سرویس‌های اپ accounts.

منطق OTP اینجا متمرکزه — نه توی view.

─── Rate Limiting: ───
از Django cache استفاده می‌کنیم (سبک‌تر از DB).
توی dev: LocMemCache
توی production: Redis
"""

import logging
import random
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.utils.phone import normalize_phone
from apps.core.utils.requests import get_client_ip

from .constants import (
    OTP_EXPIRY_MINUTES,
    OTP_LENGTH,
    OTP_MAX_ATTEMPTS,
    OTP_RATE_LIMIT_PER_HOUR,
    OTP_RESEND_COOLDOWN_SECONDS,
)
from .models import OTPCode, User

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Cache Keys
# ═══════════════════════════════════════════════════════════════

RATE_LIMIT_KEY = "otp:rate:{phone}"
COOLDOWN_KEY = "otp:cooldown:{phone}"
IP_RATE_LIMIT_KEY = "otp:ip:{ip}"

# ─── IP rate limit (جلوگیری از اسپم از یه IP) ───
IP_RATE_LIMIT_PER_HOUR = 20


# ═══════════════════════════════════════════════════════════════
#  Exceptions
# ═══════════════════════════════════════════════════════════════


class OTPError(ValidationError):
    """خطای عمومی OTP."""


class OTPRateLimitError(OTPError):
    """تعداد درخواست زیاد."""


class OTPCooldownError(OTPError):
    """فاصله‌ی بین دو درخواست کمه."""


class OTPInvalidError(OTPError):
    """کد اشتباه یا منقضی."""


class OTPMaxAttemptsError(OTPError):
    """تعداد تلاش‌ها از حد گذشت."""


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def generate_otp_code() -> str:
    """تولید کد OTP تصادفی."""
    min_val = 10 ** (OTP_LENGTH - 1)
    max_val = (10**OTP_LENGTH) - 1
    return str(random.randint(min_val, max_val))


def _check_rate_limit(phone: str) -> None:
    """
    چک rate limit بر اساس cache.

    Raises:
        OTPRateLimitError
    """
    key = RATE_LIMIT_KEY.format(phone=phone)
    count = cache.get(key, 0)

    if count >= OTP_RATE_LIMIT_PER_HOUR:
        logger.warning(f"OTP rate limit exceeded for {phone}")
        raise OTPRateLimitError(
            "تعداد درخواست‌های شما زیاده. لطفاً بعداً امتحان کنید."
        )


def _check_ip_rate_limit(ip: str | None) -> None:
    """
    چک rate limit بر اساس IP.

    Raises:
        OTPRateLimitError
    """
    if not ip:
        return

    key = IP_RATE_LIMIT_KEY.format(ip=ip)
    count = cache.get(key, 0)

    if count >= IP_RATE_LIMIT_PER_HOUR:
        logger.warning(f"OTP IP rate limit exceeded for {ip}")
        raise OTPRateLimitError(
            "تعداد درخواست‌های شما زیاده. لطفاً بعداً امتحان کنید."
        )


def _check_cooldown(phone: str) -> None:
    """
    چک cooldown بین دو درخواست.

    ─── نکته: ───
    cache مقدار `cooldown_until` (datetime) رو نگه می‌داره، نه True.
    """
    key = COOLDOWN_KEY.format(phone=phone)
    cooldown_until = cache.get(key)

    if cooldown_until:
        seconds_left = int(
            (cooldown_until - timezone.now()).total_seconds()
        )
        if seconds_left > 0:
            raise OTPCooldownError(
                f"لطفاً {seconds_left} ثانیه دیگه دوباره امتحان کنید."
            )

def _increment_rate_limit(phone: str, ip: str | None) -> None:
    """افزایش شمارنده‌ی rate limit."""
    # ─── phone ───
    phone_key = RATE_LIMIT_KEY.format(phone=phone)
    try:
        cache.incr(phone_key)
    except ValueError:
        cache.set(phone_key, 1, timeout=3600)

    # ─── ip ───
    if ip:
        ip_key = IP_RATE_LIMIT_KEY.format(ip=ip)
        try:
            cache.incr(ip_key)
        except ValueError:
            cache.set(ip_key, 1, timeout=3600)


def _set_cooldown(phone: str) -> None:
    """ست کردن cooldown (با datetime)."""
    key = COOLDOWN_KEY.format(phone=phone)
    cooldown_until = timezone.now() + timedelta(
        seconds=OTP_RESEND_COOLDOWN_SECONDS
    )
    cache.set(key, cooldown_until, timeout=OTP_RESEND_COOLDOWN_SECONDS)


# ═══════════════════════════════════════════════════════════════
#  Send OTP
# ═══════════════════════════════════════════════════════════════


def send_otp(
    phone: str,
    request=None,
) -> OTPCode:
    """
    ارسال کد OTP به شماره.

    ─── مراحل: ───
    1. نرمال‌سازی شماره
    2. چک rate limit (phone + ip)
    3. چک cooldown
    4. باطل کردن OTP های قبلی
    5. ساخت OTP جدید
    6. ارسال با SMS backend
    7. افزایش شمارنده‌ها
    """
    # ─── ۱. نرمال‌سازی ───
    normalized = normalize_phone(phone)
    if not normalized:
        raise OTPError("شماره موبایل نامعتبره.")

    # ─── IP ───
    ip = get_client_ip(request) if request else None

    # ─── ۲. Rate limit ───
    _check_rate_limit(normalized)
    _check_ip_rate_limit(ip)

    # ─── ۳. Cooldown ───
    _check_cooldown(normalized)

    # ─── ۴. باطل کردن OTP های قبلی ───
    OTPCode.objects.invalidate_previous(normalized)

    # ─── ۵. ساخت OTP جدید ───
    code = generate_otp_code()
    otp = OTPCode.objects.create_otp(
        phone=normalized,
        code=code,
        expiry_minutes=OTP_EXPIRY_MINUTES,
    )

    # ─── ۶. اطلاعات اضافی ───
    if request:
        otp.ip_address = ip
        otp.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
        otp.save(update_fields=["ip_address", "user_agent"])

    # ─── ۷. ارسال SMS ───
    from apps.notifications.services import send_sms

    message = f"کد ورود شما به آرایشیار: {code}\nاعتبار: {OTP_EXPIRY_MINUTES} دقیقه"
    try:
        send_sms(normalized, message)
    except Exception as exc:
        logger.exception(f"Failed to send OTP SMS to {normalized}: {exc}")

    # ─── ۸. افزایش شمارنده‌ها ───
    _increment_rate_limit(normalized, ip)
    _set_cooldown(normalized)

    # ─── لاگ امن ───
    if settings.DEBUG:
        logger.info(f"[DEBUG] OTP for {normalized}: {code}")
    else:
        logger.info(f"OTP sent to {normalized}")

    return otp


# ═══════════════════════════════════════════════════════════════
#  Verify OTP
# ═══════════════════════════════════════════════════════════════


def verify_otp(phone: str, code: str) -> OTPCode:
    """
    تأیید کد OTP.

    ─── امنیت: ───
    تلاش‌های اشتباه روی خود OTPCode ذخیره میشه (نه cache).
    """
    normalized = normalize_phone(phone)
    if not normalized:
        raise OTPInvalidError("شماره موبایل نامعتبره.")

    code = code.strip()
    if not code or not code.isdigit() or len(code) != OTP_LENGTH:
        raise OTPInvalidError("کد وارد‌شده معتبر نیست.")

    # ─── آخرین OTP فعال این شماره ───
    otp = (
        OTPCode.objects.filter(phone=normalized, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not otp:
        raise OTPInvalidError("کدی برای این شماره ثبت نشده.")

    # ─── چک منقضی ───
    if otp.is_expired:
        otp.mark_as_used()
        raise OTPInvalidError("کد منقضی شده. لطفاً دوباره درخواست کنید.")

    # ─── چک تعداد تلاش ───
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        otp.mark_as_used()
        raise OTPMaxAttemptsError(
            "تعداد تلاش‌های شما زیاد شده. لطفاً کد جدید درخواست کنید."
        )

    # ─── چک کد ───
    if otp.code != code:
        otp.increment_attempts()
        remaining = OTP_MAX_ATTEMPTS - otp.attempts
        raise OTPInvalidError(
            f"کد اشتباهه. {remaining} تلاش دیگه دارید."
        )

    # ─── موفق ───
    otp.mark_as_used()

    # ─── پاک کردن rate limit بعد از موفقیت ───
    cache.delete(RATE_LIMIT_KEY.format(phone=normalized))
    cache.delete(COOLDOWN_KEY.format(phone=normalized))

    logger.info(f"OTP verified for {normalized}")
    return otp