"""
تست‌های OTP flow.
"""

import pytest
from django.utils import timezone

from apps.accounts.models import OTPCode, User
from apps.accounts.services import (
    OTPCooldownError,
    OTPInvalidError,
    OTPMaxAttemptsError,
    OTPRateLimitError,
    send_otp,
    verify_otp,
)


@pytest.mark.django_db
class TestSendOTP:
    """تست‌های send_otp."""

    def test_send_otp_creates_record(self):
        otp = send_otp("09123456789")
        assert otp.phone == "09123456789"
        assert len(otp.code) == 6
        assert otp.is_used is False
        assert otp.expires_at > timezone.now()

    def test_send_otp_normalizes_phone(self):
        otp = send_otp("+989123456789")
        assert otp.phone == "09123456789"

    def test_send_otp_invalid_phone(self):
        with pytest.raises(Exception):
            send_otp("invalid")

    def test_send_otp_cooldown(self):
        send_otp("09123456789")
        with pytest.raises(OTPCooldownError):
            send_otp("09123456789")

    def test_send_otp_rate_limit(self):
        from django.core.cache import cache

        for i in range(5):
            send_otp("09123456789")
            cache.delete(f"otp:cooldown:09123456789")

        with pytest.raises(OTPRateLimitError):
            send_otp("09123456789")


@pytest.mark.django_db
class TestVerifyOTP:
    """تست‌های verify_otp."""

    def test_verify_correct_code(self):
        otp = send_otp("09123456789")
        verified = verify_otp("09123456789", otp.code)
        assert verified.pk == otp.pk
        assert verified.is_used is True
        assert verified.used_at is not None

    def test_verify_wrong_code(self):
        otp = send_otp("09123456789")
        with pytest.raises(OTPInvalidError):
            verify_otp("09123456789", "000000")

        otp.refresh_from_db()
        assert otp.attempts == 1

    def test_verify_expired_code(self):
        otp = send_otp("09123456789")
        otp.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        otp.save(update_fields=["expires_at"])

        with pytest.raises(OTPInvalidError):
            verify_otp("09123456789", otp.code)

    def test_verify_max_attempts(self):
        otp = send_otp("09123456789")

        for i in range(5):
            try:
                verify_otp("09123456789", "000000")
            except OTPInvalidError:
                pass

        with pytest.raises(OTPMaxAttemptsError):
            verify_otp("09123456789", otp.code)