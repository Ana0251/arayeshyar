"""
تست‌های تبدیل تاریخ شمسی/میلادی.

─── نکته مهم: ───
این تست‌ها مطمئن میشن که datetimeهای UTC به درستی به Tehran
تبدیل میشن (باگ قبلی: نمایش UTC).
"""

from datetime import datetime, timezone as dt_timezone

import pytest
from django.utils import timezone

from apps.core.templatetags.jalali import (
    to_jalali,
    to_jalali_datetime,
    to_jalali_long,
)


# ═══════════════════════════════════════════════════════════════
#  to_jalali (تاریخ)
# ═══════════════════════════════════════════════════════════════


class TestToJalali:
    """تست‌های to_jalali."""

    def test_gregorian_date(self):
        """تاریخ میلادی به شمسی."""
        from datetime import date

        result = to_jalali(date(2024, 9, 26))
        assert result == "1403/07/05"

    def test_aware_datetime_uses_tehran(self):
        """
        ─── نکته مهم: ───
        datetime aware (UTC) باید به Tehran تبدیل بشه، بعد شمسی.
        """
        # 2024-09-26 ساعت 00:30 UTC = 2024-09-26 ساعت 04:00 Tehran
        # ─── نکته: از dt_timezone.utc استفاده کن (نه django.utils.timezone.utc) ───
        dt_utc = datetime(2024, 9, 26, 0, 30, tzinfo=dt_timezone.utc)
        result = to_jalali(dt_utc)
        assert result == "1403/07/05"

    def test_none(self):
        """None → رشته خالی."""
        assert to_jalali(None) == ""


# ═══════════════════════════════════════════════════════════════
#  to_jalali_datetime
# ═══════════════════════════════════════════════════════════════


class TestToJalaliDatetime:
    """تست‌های to_jalali_datetime."""

    def test_utc_to_tehran_conversion(self):
        """
        ─── باگ قبلی: ───
        ساعت UTC نمایش داده میشد، نه Tehran.

        ─── تست: ───
        22:30 UTC = 02:00 Tehran (+1 روز)
        """
        # 2024-09-26 ساعت 22:30 UTC = 2024-09-27 ساعت 02:00 Tehran
        dt_utc = datetime(2024, 9, 26, 22, 30, tzinfo=dt_timezone.utc)
        result = to_jalali_datetime(dt_utc)
        # ─── باید ساعت 02:00 و تاریخ 1403/07/06 باشه ───
        assert "02:00" in result
        assert "1403/07/06" in result

    def test_none(self):
        """None → رشته خالی."""
        assert to_jalali_datetime(None) == ""


# ═══════════════════════════════════════════════════════════════
#  to_jalali_long
# ═══════════════════════════════════════════════════════════════


class TestToJalaliLong:
    """تست‌های to_jalali_long."""

    def test_long_format(self):
        """تاریخ طولانی با نام ماه."""
        from datetime import date

        result = to_jalali_long(date(2024, 9, 26))
        # ─── jdatetime با locale انگلیسی «Mehr» نشون میده، نه «مهر» ───
        # ─── پس چک می‌کنیم که «Mehr» یا «مهر» باشه ───
        assert ("مهر" in result) or ("Mehr" in result)
        assert "1403" in result