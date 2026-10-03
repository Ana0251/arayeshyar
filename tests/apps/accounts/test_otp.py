"""
تست‌های OTP flow.

─── نکته: ───
از ConsoleSMSBackend استفاده می‌کنیم که توی dev پیش‌فرضه.
"""

import pytest
from django.utils import timezone

from apps.accounts.constants import Role
from apps.accounts.models import OTPCode, User
from apps.accounts.services import (
    OTPCooldownError,
    OTPInvalidError,
    OTPRateLimitError,
    send_otp,
    verify_otp,
)


# ═══════════════════════════════════════════════════════════════
#  Send OTP
# ═══════════════════════════════════════════════════════════════


class TestSendOTP:
    """تست‌های send_otp."""

    def test_send_otp_creates_record(self, db):
        """ارسال OTP → رکورد ساخته میشه."""
        otp = send_otp("09123456789")

        assert otp.phone == "09123456789"
        assert len(otp.code) == 6
        assert otp.is_used is False
        assert otp.expires_at > timezone.now()

    def test_send_otp_normalizes_phone(self, db):
        """شماره نرمال میشه."""
        otp = send_otp("+989123456789")
        assert otp.phone == "09123456789"

    def test_send_otp_invalid_phone(self, db):
        """شماره نامعتبر → خطا."""
        with pytest.raises(Exception):
            send_otp("invalid")

    def test_send_otp_cooldown(self, db):
        """ارسال مجدد بلافاصله → cooldown."""
        send_otp("09123456789")

        with pytest.raises(OTPCooldownError):
            send_otp("09123456789")

    def test_send_otp_rate_limit(self, db):
        """بیش از ۵ بار در ساعت → rate limit."""
        from django.core.cache import cache
        from django.utils import timezone as tz

        # ─── ۵ بار ارسال (cooldown رو هر بار پاک کن) ───
        for i in range(5):
            send_otp("09123456789")
            # ─── cooldown cache رو پاک کن ───
            cache.delete(f"otp:cooldown:09123456789")

        # ─── درخواست ششم → rate limit ───
        with pytest.raises(OTPRateLimitError):
            send_otp("09123456789")


# ═══════════════════════════════════════════════════════════════
#  Verify OTP
# ═══════════════════════════════════════════════════════════════


class TestVerifyOTP:
    """تست‌های verify_otp."""

    def test_verify_correct_code(self, db):
        """کد صحیح → تأیید."""
        otp = send_otp("09123456789")
        verified = verify_otp("09123456789", otp.code)

        assert verified.pk == otp.pk
        assert verified.is_used is True
        assert verified.used_at is not None

    def test_verify_wrong_code(self, db):
        """کد اشتباه → خطا + attempts++. """
        otp = send_otp("09123456789")

        with pytest.raises(OTPInvalidError):
            verify_otp("09123456789", "000000")

        otp.refresh_from_db()
        assert otp.attempts == 1

    def test_verify_expired_code(self, db):
        """کد منقضی → خطا."""
        otp = send_otp("09123456789")

        # ─── منقضی کن ───
        otp.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        otp.save(update_fields=["expires_at"])

        with pytest.raises(OTPInvalidError):
            verify_otp("09123456789", otp.code)

    def test_verify_max_attempts(self, db):
        """بعد از ۵ تلاش اشتباه → قفل."""
        otp = send_otp("09123456789")

        # ─── ۵ بار کد اشتباه ───
        for i in range(5):
            try:
                verify_otp("09123456789", "000000")
            except OTPInvalidError:
                pass

        # ─── تلاش ششم → قفل ───
        from apps.accounts.services import OTPMaxAttemptsError

        with pytest.raises(OTPMaxAttemptsError):
            verify_otp("09123456789", otp.code)