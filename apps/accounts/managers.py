"""Managerهای حساب کاربری؛ ورود با شماره موبایل و رمز عبور."""
from typing import Any
from datetime import timedelta
from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils import timezone
from apps.core.utils.phone import normalize_phone
from .constants import Role


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone: str, password: str | None = None, **extra_fields: Any):
        phone = normalize_phone(phone)
        if not phone:
            raise ValueError("شماره موبایل معتبر الزامیه.")

        email = (extra_fields.pop("email", None) or "").strip().lower() or None
        if email:
            email = self.normalize_email(email)

        user = self.model(phone=phone, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, phone: str, password: str | None = None, **extra_fields: Any):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", Role.CUSTOMER)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone: str, password: str | None = None, **extra_fields: Any):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", Role.ADMIN)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser باید دسترسی staff و superuser داشته باشه.")
        return self._create_user(phone, password, **extra_fields)

    def get_by_phone(self, phone: str):
        normalized = normalize_phone(phone)
        if not normalized:
            return None
        try:
            return self.get(phone=normalized)
        except self.model.DoesNotExist:
            return None


class OTPCodeManager(models.Manager):
    """فعلاً فقط برای سازگاری و استفاده احتمالی آینده نگه داشته شده."""
    def create_email_otp(self, email: str, code_hash: str, expiry_minutes: int = 2):
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        return self.create(email=email, code_hash=code_hash, expires_at=expires_at)

    def invalidate_previous_email(self, email: str) -> int:
        return self.filter(email__iexact=email, is_used=False).update(is_used=True)

    def cleanup_expired(self) -> int:
        return self.filter(expires_at__lt=timezone.now()).delete()[0]
