"""ارسال و تأیید OTP ایمیلی با rate-limit و ذخیره هش‌شده کد."""
import logging
import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.utils import timezone
from apps.core.utils.requests import get_client_ip
from .constants import OTP_EXPIRY_MINUTES, OTP_LENGTH, OTP_MAX_ATTEMPTS, OTP_RATE_LIMIT_PER_HOUR, OTP_RESEND_COOLDOWN_SECONDS
from .models import OTPCode

logger = logging.getLogger(__name__)
EMAIL_RATE_LIMIT_KEY = "otp:email:rate:{email}"
EMAIL_COOLDOWN_KEY = "otp:email:cooldown:{email}"
IP_RATE_LIMIT_KEY = "otp:ip:{ip}"
IP_RATE_LIMIT_PER_HOUR = 20


class OTPError(ValidationError): pass
class OTPRateLimitError(OTPError): pass
class OTPCooldownError(OTPError): pass
class OTPInvalidError(OTPError): pass
class OTPMaxAttemptsError(OTPError): pass


def _message(exc):
    values = getattr(exc, "messages", None)
    return str(values[0]) if values else str(exc)


def normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    try:
        validate_email(normalized)
    except ValidationError as exc:
        raise OTPError("ایمیل معتبر نیست.") from exc
    return normalized


def generate_otp_code() -> str:
    low = 10 ** (OTP_LENGTH - 1)
    high = (10 ** OTP_LENGTH) - 1
    return str(secrets.randbelow(high - low + 1) + low)


def _check_ip_limit(ip):
    if ip and cache.get(IP_RATE_LIMIT_KEY.format(ip=ip), 0) >= IP_RATE_LIMIT_PER_HOUR:
        raise OTPRateLimitError("تعداد درخواست‌ها از این اتصال زیاد شده. کمی بعد دوباره امتحان کن.")


def _increment(key, timeout=3600):
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=timeout)


def send_email_otp(email: str, request=None) -> OTPCode:
    email = normalize_email(email)
    ip = get_client_ip(request) if request else None
    rate_key = EMAIL_RATE_LIMIT_KEY.format(email=email)
    cooldown_key = EMAIL_COOLDOWN_KEY.format(email=email)

    if cache.get(rate_key, 0) >= OTP_RATE_LIMIT_PER_HOUR:
        raise OTPRateLimitError("تعداد درخواست‌های کد زیاد شده. کمی بعد دوباره امتحان کن.")
    _check_ip_limit(ip)

    cooldown_until = cache.get(cooldown_key)
    if cooldown_until:
        left = int((cooldown_until - timezone.now()).total_seconds())
        if left > 0:
            raise OTPCooldownError(f"لطفاً {left} ثانیه دیگه دوباره امتحان کن.")

    OTPCode.objects.invalidate_previous_email(email)
    code = generate_otp_code()
    otp = OTPCode.objects.create_email_otp(email, make_password(code), OTP_EXPIRY_MINUTES)
    if request:
        otp.ip_address = ip
        otp.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
        otp.save(update_fields=["ip_address", "user_agent"])

    send_mail(
        "کد ورود آرایشیار",
        f"کد ورود شما به آرایشیار: {code}\nاعتبار: {OTP_EXPIRY_MINUTES} دقیقه",
        getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@arayeshyar.local"),
        [email],
        fail_silently=False,
    )

    _increment(rate_key)
    if ip:
        _increment(IP_RATE_LIMIT_KEY.format(ip=ip))
    cache.set(cooldown_key, timezone.now() + timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS), timeout=OTP_RESEND_COOLDOWN_SECONDS)

    if settings.DEBUG:
        logger.info("[DEBUG] Email OTP for %s: %s", email, code)
    return otp


def verify_email_otp(email: str, code: str) -> OTPCode:
    email = normalize_email(email)
    code = (code or "").strip()
    if not code.isdigit() or len(code) != OTP_LENGTH:
        raise OTPInvalidError("کد واردشده معتبر نیست.")

    otp = OTPCode.objects.filter(email__iexact=email, is_used=False).order_by("-created_at").first()
    if not otp:
        raise OTPInvalidError("کد فعالی برای این ایمیل وجود نداره.")
    if otp.is_expired:
        otp.mark_as_used()
        raise OTPInvalidError("کد منقضی شده. کد جدید بگیر.")
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        otp.mark_as_used()
        raise OTPMaxAttemptsError("تعداد تلاش‌ها زیاد شده. کد جدید بگیر.")
    if not check_password(code, otp.code_hash):
        otp.increment_attempts()
        remaining = max(0, OTP_MAX_ATTEMPTS - otp.attempts)
        raise OTPInvalidError(f"کد اشتباهه. {remaining} تلاش دیگه داری.")

    otp.mark_as_used()
    cache.delete(EMAIL_RATE_LIMIT_KEY.format(email=email))
    cache.delete(EMAIL_COOLDOWN_KEY.format(email=email))
    return otp
