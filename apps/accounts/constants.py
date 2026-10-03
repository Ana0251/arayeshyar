"""
ثابت‌های اپ accounts.

همه‌ی مقادیر قابل تنظیم اینجا جمع شدن تا یک جا قابل تغییر باشن.
"""

from django.conf import settings

# ═══════════════════════════════════════════════════════════════
#  OTP
# ═══════════════════════════════════════════════════════════════

OTP_LENGTH: int = getattr(settings, "OTP_LENGTH", 6)
OTP_EXPIRY_MINUTES: int = getattr(settings, "OTP_EXPIRY_MINUTES", 2)
OTP_MAX_ATTEMPTS: int = getattr(settings, "OTP_MAX_ATTEMPTS", 5)
OTP_RATE_LIMIT_PER_HOUR: int = getattr(settings, "OTP_RATE_LIMIT_PER_HOUR", 5)

# ─── سقف رزرو ───
OTP_RESEND_COOLDOWN_SECONDS: int = 60  # حداقل ۶۰ ثانیه بین دو درخواست

# ═══════════════════════════════════════════════════════════════
#  Phone
# ═══════════════════════════════════════════════════════════════

PHONE_LENGTH: int = 11
PHONE_PREFIX: str = "09"


# ═══════════════════════════════════════════════════════════════
#  نقش‌ها
# ═══════════════════════════════════════════════════════════════


class Role:
    """نقش‌های کاربری (توی models.User استفاده میشه)."""

    CUSTOMER = "customer"
    BUSINESS_OWNER = "business_owner"
    ADMIN = "admin"

    CHOICES = [
        (CUSTOMER, "مشتری"),
        (BUSINESS_OWNER, "صاحب کسب‌وکار"),
        (ADMIN, "مدیر"),
    ]

    ALL = [CUSTOMER, BUSINESS_OWNER, ADMIN]