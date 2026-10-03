"""
Helper های تاریخ و timezone.

─── قاعده‌ی کلی پروژه: ───
- همه‌ی datetime ها توی DB به UTC ذخیره میشن
- همه‌ی محاسبات به UTC انجام میشن
- فقط برای نمایش، به Tehran تبدیل میشن

─── استفاده: ───
    utc_dt = local_to_utc(local_dt)        # Tehran → UTC
    local_dt = utc_to_local(utc_dt)        # UTC → Tehran
"""

from datetime import datetime

from django.utils import timezone


# ═══════════════════════════════════════════════════════════════
#  Timezone Conversion
# ═══════════════════════════════════════════════════════════════


def local_to_utc(dt: datetime) -> datetime:
    """
    تبدیل datetime تهران (aware یا naive) به UTC.

    ─── نکته: ───
    اگه dt aware باشه → مستقیم convert میشه
    اگه dt naive باشه → اول timezone فعلی (Tehran) می‌گیره، بعد UTC
    """
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt.astimezone(timezone.utc)


def utc_to_local(dt: datetime) -> datetime:
    """
    تبدیل datetime UTC به Tehran.

    ─── نکته: ───
    اگه dt naive باشه → فرض می‌کنه UTC است و بعد local می‌کنه
    """
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return timezone.localtime(dt)


def to_tehran(dt: datetime) -> datetime:
    """
    Alias برای utc_to_local — برای خوانایی بیشتر.

    ─── استفاده: ───
        local_dt = to_tehran(appointment.start_at)
    """
    return utc_to_local(dt)