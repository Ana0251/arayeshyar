"""
Manager های سفارشی برای مدل‌های accounts.
"""

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils import timezone

from apps.core.utils.phone import normalize_phone

from .constants import Role

if TYPE_CHECKING:
    from .models import OTPCode, User


class UserManager(BaseUserManager):
    """
    Manager سفارشی برای User.

    چون USERNAME_FIELD = 'phone'، متدهای create_user و create_superuser
    باید بر اساس phone باشن.
    """

    use_in_migrations = True

    def _create_user(
        self,
        phone: str,
        password: str | None,
        **extra_fields: Any,
    ) -> "User":
        """ساخت کاربر با phone."""
        if not phone:
            raise ValueError("شماره موبایل الزامیه.")

        # ─── نرمال‌سازی شماره ───
        phone = normalize_phone(phone)
        if not phone:
            raise ValueError("شماره موبایل نامعتبره.")

        user = self.model(phone=phone, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(
        self,
        phone: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """ساخت کاربر عادی."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", Role.CUSTOMER)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(
        self,
        phone: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """ساخت superuser (برای admin)."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser باید is_staff=True باشه.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser باید is_superuser=True باشه.")

        return self._create_user(phone, password, **extra_fields)

    def get_by_phone(self, phone: str) -> "User | None":
        """گرفتن کاربر با شماره موبایل (نرمال‌شده)."""
        normalized = normalize_phone(phone)
        if not normalized:
            return None

        try:
            return self.get(phone=normalized)
        except self.model.DoesNotExist:
            return None


class OTPCodeManager(models.Manager):
    """Manager برای OTPCode."""

    def create_otp(
        self,
        phone: str,
        code: str,
        expiry_minutes: int = 2,
    ) -> "OTPCode":
        """ساخت کد OTP جدید."""
        from datetime import timedelta

        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        return self.create(
            phone=phone,
            code=code,
            expires_at=expires_at,
        )

    def get_valid_otp(self, phone: str, code: str) -> "OTPCode | None":
        """
        گرفتن OTP معتبر (استفاده‌نشده + منقضی‌نشده).

        اگه پیدا نشد، None برمی‌گردونه.
        """
        return (
            self.filter(
                phone=phone,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )

    def invalidate_previous(self, phone: str) -> int:
        """همه‌ی OTP های قبلی این شماره رو باطل کن."""
        return self.filter(phone=phone, is_used=False).update(is_used=True)

    def cleanup_expired(self) -> int:
        """حذف OTP های منقضی‌شده (برای cron)."""
        return self.filter(expires_at__lt=timezone.now()).delete()[0]