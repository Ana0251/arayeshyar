"""
Helper های تاریخ و timezone پروژه.

- datetime ها در DB به UTC ذخیره می‌شوند.
- تبدیل timezone برای محاسبات/نمایش حفظ شده است.
- نمایش تاریخ برای کاربر می‌تواند به شمسی تبدیل شود.
"""
from __future__ import annotations

from datetime import date, datetime

import jdatetime
from django.utils import timezone


# ═══════════════════════════════════════════════════════════════
# Timezone conversion (توابع قدیمی پروژه - برای سازگاری)
# ═══════════════════════════════════════════════════════════════


def local_to_utc(dt: datetime) -> datetime:
    """تبدیل datetime محلی (Tehran/current timezone) به UTC."""
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt.astimezone(timezone.utc)


def utc_to_local(dt: datetime) -> datetime:
    """تبدیل datetime UTC به timezone محلی پروژه."""
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return timezone.localtime(dt)


def to_tehran(dt: datetime) -> datetime:
    """Alias سازگار با کدهای فعلی پروژه."""
    return utc_to_local(dt)


# ═══════════════════════════════════════════════════════════════
# Jalali display helpers
# ═══════════════════════════════════════════════════════════════


def to_jalali_date(value: date | datetime | None, fmt: str = "%Y/%m/%d") -> str:
    """تبدیل date/datetime میلادی به رشته تاریخ شمسی."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        value = value.date()
    return jdatetime.date.fromgregorian(date=value).strftime(fmt)


def to_jalali_datetime(value: datetime | None, fmt: str = "%Y/%m/%d - %H:%M") -> str:
    """تبدیل datetime به رشته تاریخ/ساعت شمسی با timezone محلی."""
    if value is None:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return jdatetime.datetime.fromgregorian(datetime=value).strftime(fmt)


def jalali_date_and_time(value: datetime | None) -> tuple[str, str]:
    """خروجی مناسب پیامک/اعلان: (تاریخ شمسی، ساعت محلی)."""
    if value is None:
        return "", ""
    local_value = timezone.localtime(value) if timezone.is_aware(value) else value
    return to_jalali_date(local_value), local_value.strftime("%H:%M")
