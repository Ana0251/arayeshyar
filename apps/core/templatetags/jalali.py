"""
فیلترهای تاریخ شمسی برای template ها.

استفاده:
    {% load jalali %}

    {{ obj.date|to_jalali }}              → 1403/07/05
    {{ obj.date|to_jalali:"%d %B %Y" }}   → 05 مهر 1403
    {{ obj.datetime|to_jalali_datetime }} → 1403/07/05 - 14:30
"""

from datetime import date, datetime

import jdatetime
from django import template
from django.utils import timezone

register = template.Library()


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _to_local(value):
    """
    تبدیل datetime aware به timezone محلی (Tehran).

    ─── نکته: ───
    اگه value naive باشه یا date (نه datetime) باشه، دست‌نخورده برمی‌گرده.
    """
    if isinstance(value, datetime) and timezone.is_aware(value):
        return timezone.localtime(value)
    return value


# ═══════════════════════════════════════════════════════════════
#  Filters
# ═══════════════════════════════════════════════════════════════


@register.filter
def to_jalali(value, fmt: str = "%Y/%m/%d") -> str:
    """
    تبدیل تاریخ میلادی به شمسی.

    Args:
        value: date یا datetime میلادی
        fmt: فرمت خروجی (پیش‌فرض %Y/%m/%d)

    Returns:
        رشته‌ی تاریخ شمسی
    """
    if not value:
        return ""

    try:
        # ─── اگه datetime aware باشه، به Tehran تبدیل کن ───
        value = _to_local(value)

        # ─── اگه datetime باشه، date رو استخراج کن ───
        if isinstance(value, datetime):
            value = value.date()

        if not isinstance(value, date):
            return str(value)

        jalali_date = jdatetime.date.fromgregorian(date=value)
        return jalali_date.strftime(fmt)
    except (ValueError, AttributeError, TypeError):
        return str(value)


@register.filter
def to_jalali_datetime(value, fmt: str = "%Y/%m/%d - %H:%M") -> str:
    """
    تبدیل datetime میلادی به شمسی با ساعت.

    ─── نکته مهم: ───
    datetime توی DB به UTC ذخیره میشه. این فیلتر اول به
    timezone محلی (Tehran) تبدیل می‌کنه، بعد شمسی.

    Args:
        value: datetime میلادی
        fmt: فرمت خروجی

    Returns:
        رشته‌ی datetime شمسی
    """
    if not value:
        return ""

    try:
        if not isinstance(value, datetime):
            return str(value)

        # ─── تبدیل به Tehran ───
        value = _to_local(value)

        jalali_dt = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_dt.strftime(fmt)
    except (ValueError, AttributeError, TypeError):
        return str(value)




@register.simple_tag
def jalali_today(fmt: str = "%Y/%m/%d") -> str:
    """
    تاریخ امروز به شمسی.

    ─── استفاده: ───
        {% jalali_today %}              → 1403/07/05
        {% jalali_today "%d %B %Y" %}   → 05 مهر 1403
    """
    today = jdatetime.date.today()
    return today.strftime(fmt)

# ═══════════════════════════════════════════════════════════════
#  ماه‌های فارسی
# ═══════════════════════════════════════════════════════════════

JALALI_MONTHS_FA = [
    "فروردین", "اردیبهشت", "خرداد",
    "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر",
    "دی", "بهمن", "اسفند",
]


@register.filter
def to_jalali_long(value) -> str:
    """
    تاریخ شمسی با نام ماه فارسی.

    مثال: ۰۵ مهر ۱۴۰۳
    """
    if not value:
        return ""

    try:
        value = _to_local(value)

        if isinstance(value, datetime):
            value = value.date()

        if not isinstance(value, date):
            return str(value)

        jalali_date = jdatetime.date.fromgregorian(date=value)
        month_name = JALALI_MONTHS_FA[jalali_date.month - 1]
        return f"{jalali_date.day:02d} {month_name} {jalali_date.year}"
    except (ValueError, AttributeError, TypeError):
        return str(value)