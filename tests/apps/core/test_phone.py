"""
تست‌های نرمال‌سازی شماره موبایل.
"""

import pytest

from apps.core.utils.phone import mask_phone, normalize_phone, validate_phone


class TestNormalizePhone:
    """تست‌های normalize_phone."""

    @pytest.mark.parametrize(
        "input_phone,expected",
        [
            # فرمت استاندارد
            ("09123456789", "09123456789"),
            # با فاصله
            ("0912 345 6789", "09123456789"),
            # با خط تیره
            ("0912-345-6789", "09123456789"),
            # با پرانتز
            ("0912(345)6789", "09123456789"),
            # با نقطه
            ("0912.345.6789", "09123456789"),
            # بین‌المللی +98
            ("+989123456789", "09123456789"),
            # بین‌المللی 0098
            ("00989123456789", "09123456789"),
            # بین‌المللی 98
            ("989123456789", "09123456789"),
            # بدون صفر
            ("9123456789", "09123456789"),
            # ارقام فارسی
            ("۰۹۱۲۳۴۵۶۷۸۹", "09123456789"),
            # ارقام عربی
            ("٠٩١٢٣٤٥٦٧٨٩", "09123456789"),
            # با whitespace اضافی
            ("  09123456789  ", "09123456789"),
        ],
    )
    def test_valid_phones(self, input_phone, expected):
        """شماره‌های معتبر → نرمال میشن."""
        assert normalize_phone(input_phone) == expected

    @pytest.mark.parametrize(
        "invalid_phone",
        [
            None,
            "",
            "123",
            "0912345678",
            "091234567890",
            "0812345678",
            "1234567890",
            "abc",
            "0912-345-678",
            "+1234567890",
        ],
    )
    def test_invalid_phones(self, invalid_phone):
        """شماره‌های نامعتبر → None."""
        assert normalize_phone(invalid_phone) is None


class TestMaskPhone:
    """تست‌های mask_phone."""

    def test_mask_standard(self):
        assert mask_phone("09123456789") == "0912***6789"

    def test_mask_with_international(self):
        assert mask_phone("+989123456789") == "0912***6789"

    def test_mask_invalid(self):
        assert mask_phone("invalid") == "invalid"


class TestValidatePhone:
    """تست‌های validate_phone."""

    def test_valid(self):
        # نباید خطا بده
        validate_phone("09123456789")

    def test_invalid(self):
        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            validate_phone("invalid")