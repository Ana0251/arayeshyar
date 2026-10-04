"""
تست‌های تبدیل تاریخ شمسی/میلادی.
"""

from datetime import date, datetime, timezone as dt_timezone

import pytest
from django.utils import timezone

from apps.core.templatetags.jalali import (
    to_jalali,
    to_jalali_datetime,
    to_jalali_long,
)


class TestToJalali:
    """تست‌های to_jalali."""

    def test_gregorian_date(self):
        assert to_jalali(date(2024, 9, 26)) == "1403/07/05"

    def test_aware_datetime_uses_tehran(self):
        dt_utc = datetime(2024, 9, 26, 0, 30, tzinfo=dt_timezone.utc)
        assert to_jalali(dt_utc) == "1403/07/05"

    def test_naive_datetime(self):
        dt = datetime(2024, 9, 26, 12, 0)
        assert to_jalali(dt) == "1403/07/05"

    def test_none(self):
        assert to_jalali(None) == ""

    def test_empty_string(self):
        assert to_jalali("") == ""

    def test_custom_format(self):
        assert to_jalali(date(2024, 9, 26), "%Y-%m-%d") == "1403-07-05"


class TestToJalaliDatetime:
    """تست‌های to_jalali_datetime."""

    def test_utc_to_tehran_conversion(self):
        """22:30 UTC = 02:00 Tehran (+1 روز)."""
        dt_utc = datetime(2024, 9, 26, 22, 30, tzinfo=dt_timezone.utc)
        result = to_jalali_datetime(dt_utc)
        assert "02:00" in result
        assert "1403/07/06" in result

    def test_none(self):
        assert to_jalali_datetime(None) == ""


class TestToJalaliLong:
    """تست‌های to_jalali_long."""

    def test_long_format(self):
        result = to_jalali_long(date(2024, 9, 26))
        assert ("مهر" in result) or ("Mehr" in result)
        assert "1403" in result