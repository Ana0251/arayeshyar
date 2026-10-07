"""مدل‌های حساب کاربری؛ ورود اصلی با شماره موبایل و رمز عبور."""
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from .constants import Role
from .managers import OTPCodeManager, UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("ایمیل"), unique=True, null=True, blank=True, db_index=True)
    phone = models.CharField(
        _("شماره موبایل"), max_length=11, unique=True, db_index=True,
        help_text=_("شناسه ورود و شماره تماس؛ به فرمت 09XXXXXXXXX"),
    )
    role = models.CharField(_("نقش"), max_length=20, choices=Role.CHOICES, default=Role.CUSTOMER, db_index=True)
    is_active = models.BooleanField(_("فعال"), default=True)
    is_staff = models.BooleanField(_("دسترسی به ادمین"), default=False)
    date_joined = models.DateTimeField(_("تاریخ عضویت"), default=timezone.now)
    last_login_ip = models.GenericIPAddressField(_("آخرین IP ورود"), null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")
        ordering = ["-date_joined"]
        indexes = [models.Index(fields=["role", "is_active"])]

    def __str__(self):
        return self.phone or self.email or f"user-{self.pk}"

    @property
    def is_customer(self):
        return self.role == Role.CUSTOMER

    @property
    def is_business_owner(self):
        return self.role == Role.BUSINESS_OWNER

    @property
    def is_platform_admin(self):
        return self.role == Role.ADMIN

    @property
    def display_name(self):
        profile = getattr(self, "customer_profile", None)
        if profile and profile.full_name:
            return profile.full_name
        business = getattr(self, "business", None)
        if business and business.name:
            return business.name
        return self.phone or self.email or _("کاربر")

    @property
    def avatar_url(self):
        business = getattr(self, "business", None)
        if business and business.avatar:
            return business.avatar.url
        return None


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile", verbose_name=_("کاربر"), primary_key=True)
    full_name = models.CharField(_("نام کامل"), max_length=100, blank=True)
    hide_ads_banner = models.BooleanField(_("مخفی کردن بنر تبلیغاتی"), default=False)
    notes = models.TextField(_("یادداشت"), blank=True)

    class Meta:
        verbose_name = _("پروفایل مشتری")
        verbose_name_plural = _("پروفایل‌های مشتری")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.phone or self.user.email} — {self.full_name or 'بدون نام'}"


class BusinessOwnerProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="business_owner_profile", verbose_name=_("کاربر"), primary_key=True)
    national_id = models.CharField(_("کد ملی"), max_length=10, blank=True)

    class Meta:
        verbose_name = _("پروفایل صاحب کسب‌وکار")
        verbose_name_plural = _("پروفایل‌های صاحب کسب‌وکار")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.phone or self.user.email} — {self.user.display_name}"


class OTPCode(models.Model):
    email = models.EmailField(_("ایمیل"), db_index=True)
    code_hash = models.CharField(_("هش کد"), max_length=128)
    is_used = models.BooleanField(_("استفاده شده"), default=False, db_index=True)
    attempts = models.PositiveSmallIntegerField(_("تعداد تلاش‌ها"), default=0)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(_("تاریخ انقضا"), db_index=True)
    used_at = models.DateTimeField(_("تاریخ استفاده"), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_("IP"), null=True, blank=True)
    user_agent = models.CharField(_("User-Agent"), max_length=255, blank=True)

    objects = OTPCodeManager()

    class Meta:
        verbose_name = _("کد یک‌بارمصرف")
        verbose_name_plural = _("کدهای یک‌بارمصرف")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.email} — {'used' if self.is_used else 'active'}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    @property
    def seconds_until_expiry(self):
        return int((self.expires_at - timezone.now()).total_seconds())

    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

    def increment_attempts(self):
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return self.attempts

    @classmethod
    def cleanup_expired(cls, hours=24):
        cutoff = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(expires_at__lt=cutoff).delete()[0]
