"""
نرمال‌سازی و اعتبارسنجی شماره موبایل ایران.

─── چرا اینجا؟ ───
این ماژول توی چند اپ استفاده میشه (accounts, business, booking).
برای جلوگیری از import های چرخشی، توی core قرار گرفته.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .numbers import persian_to_latin


# ═══════════════════════════════════════════════════════════════
#  الگو و پیشوندها
# ═══════════════════════════════════════════════════════════════

PHONE_REGEX = re.compile(r"^09\d{9}$")

PHONE_PREFIXES = {
    "+98": "0",
    "0098": "0",
    "98": "0",
}


# ═══════════════════════════════════════════════════════════════
#  Normalize
# ═══════════════════════════════════════════════════════════════


def normalize_phone(phone: str | None) -> str | None:
    """
    نرمال‌سازی شماره موبایل به فرمت 09XXXXXXXXX.

    ─── ورودی‌های مجاز: ───
    - 09123456789    → 09123456789
    - +989123456789  → 09123456789
    - 00989123456789 → 09123456789
    - 989123456789   → 09123456789
    - 9123456789     → 09123456789
    - 0912-345-6789  → 09123456789
    - ۰۹۱۲۳۴۵۶۷۸۹   → 09123456789

    Args:
        phone: شماره ورودی

    Returns:
        شماره نرمال‌شده یا None
    """
    if not phone:
        return None

    # ─── به رشته تبدیل + حذف کاراکترهای اضافی ───
    phone = str(phone).strip()
    phone = re.sub(r"[\s\-\(\)\.]", "", phone)

    # ─── تبدیل ارقام فارسی/عربی به لاتین ───
    phone = persian_to_latin(phone)

    # ─── تبدیل فرمت‌های بین‌المللی ───
    for prefix, replacement in PHONE_PREFIXES.items():
        if phone.startswith(prefix):
            phone = replacement + phone[len(prefix):]
            break

    # ─── اگه با 9 شروع شد (بدون صفر)، صفر اضافه کن ───
    if phone.startswith("9") and len(phone) == 10:
        phone = "0" + phone

    # ─── اعتبارسنجی نهایی ───
    if not PHONE_REGEX.match(phone):
        return None

    return phone


# ═══════════════════════════════════════════════════════════════
#  Validate
# ═══════════════════════════════════════════════════════════════


def validate_phone(value: str) -> None:
    """
    اعتبارسنجی شماره موبایل (برای فرم‌ها و مدل‌ها).

    Raises:
        ValidationError: اگه شماره نامعتبر باشه.
    """
    normalized = normalize_phone(value)
    if not normalized:
        raise ValidationError(
            _("شماره موبایل نامعتبره. فرمت صحیح: 09XXXXXXXXX"),
            code="invalid_phone",
        )


# ═══════════════════════════════════════════════════════════════
#  Mask
# ═══════════════════════════════════════════════════════════════


def mask_phone(phone: str) -> str:
    """
    مخفی کردن وسط شماره برای نمایش.

    مثال: 09123456789 → 0912***6789
    """
    normalized = normalize_phone(phone)
    if not normalized:
        return phone

    return f"{normalized[:4]}***{normalized[-4:]}"