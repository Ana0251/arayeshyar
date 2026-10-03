"""
تبدیل ارقام فارسی/عربی ↔ لاتین.

─── چرا اینجا؟ ───
توی چند جا استفاده میشه:
- phone.py (نرمال‌سازی)
- forms (OTP code)
- jalali (نمایش)
"""


# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
LATIN_DIGITS = "0123456789"


# ═══════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════


def persian_to_latin(text: str) -> str:
    """
    تبدیل ارقام فارسی و عربی به لاتین.

    ─── مثال: ───
    "۰۹۱۲۳۴۵۶۷۸۹" → "09123456789"
    "٠٩١٢٣٤٥٦٧٨٩" → "09123456789"
    """
    if not text:
        return text

    translation_table = str.maketrans(
        PERSIAN_DIGITS + ARABIC_DIGITS,
        LATIN_DIGITS + LATIN_DIGITS,
    )
    return text.translate(translation_table)


def latin_to_persian(text: str) -> str:
    """
    تبدیل ارقام لاتین به فارسی.

    ─── مثال: ───
    "09123456789" → "۰۹۱۲۳۴۵۶۷۸۹"
    """
    if not text:
        return text

    translation_table = str.maketrans(
        LATIN_DIGITS,
        PERSIAN_DIGITS,
    )
    return text.translate(translation_table)