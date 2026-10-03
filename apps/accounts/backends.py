"""
Backend های احراز هویت سفارشی.

OTPBackend برای ورود با کد یک‌بارمصرف استفاده میشه.
"""

from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

if TYPE_CHECKING:
    from django.http import HttpRequest

    from .models import User

User = get_user_model()


class OTPBackend(BaseBackend):
    """
    Backend ورود با OTP.

    ─── نکته: ───
    این backend فرض می‌کنه که OTP **قبلاً** verify شده
    (توی view login_otp).

    پس فقط کاربر رو برمی‌گردونه. اگه کاربر وجود نداشته باشه،
    خودکار می‌سازیمش (register on first login).
    """

    def authenticate(
        self,
        request: "HttpRequest | None",
        phone: str | None = None,
        otp_verified: bool = False,
        **kwargs: Any,
    ) -> "User | None":
        """
        احراز هویت با phone.

        Args:
            request: HttpRequest
            phone: شماره موبایل
            otp_verified: آیا OTP verify شده؟ (باید True باشه)

        Returns:
            User یا None
        """
        if not phone or not otp_verified:
            return None

        # ─── نرمال‌سازی ───
        from apps.core.utils.phone import normalize_phone

        normalized = normalize_phone(phone)
        if not normalized:
            return None

        # ─── پیدا یا ساخت کاربر ───
        user, _created = User.objects.get_or_create(
            phone=normalized,
            defaults={
                "role": "customer",
                "is_active": True,
            },
        )

        # ─── چک فعال بودن ───
        if not user.is_active:
            return None

        return user

    def get_user(self, user_id: int) -> "User | None":
        """گرفتن کاربر با ID (برای session)."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None