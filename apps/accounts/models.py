"""
مدل‌های اپ accounts.

شامل:
- User (سفارشی با phone)
- CustomerProfile
- BusinessOwnerProfile
- OTPCode
"""

from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

from .constants import Role
from .managers import OTPCodeManager, UserManager


# ═══════════════════════════════════════════════════════════════
#  User
# ═══════════════════════════════════════════════════════════════


class User(AbstractBaseUser, PermissionsMixin):
    """
    مدل کاربر سفارشی.

    به جای username، از phone استفاده می‌کنه.
    نقش (role) مشخص می‌کنه کاربر مشتریه یا صاحب کسب‌وکار.

    ─── نکته مهم: ───
    این مدل باید از همون اول migration بشه.
    بعداً عوض کردنش خیلی دردناکه.
    """

    phone = models.CharField(
        _("شماره موبایل"),
        max_length=11,
        unique=True,
        db_index=True,
        help_text=_("به فرمت 09XXXXXXXXX"),
    )
    role = models.CharField(
        _("نقش"),
        max_length=20,
        choices=Role.CHOICES,
        default=Role.CUSTOMER,
        db_index=True,
    )
    is_active = models.BooleanField(
        _("فعال"),
        default=True,
        help_text=_("اگه False باشه، کاربر نمی‌تونه وارد بشه."),
    )
    is_staff = models.BooleanField(
        _("دسترسی به ادمین"),
        default=False,
    )
    date_joined = models.DateTimeField(
        _("تاریخ عضویت"),
        default=timezone.now,
    )
    last_login_ip = models.GenericIPAddressField(
        _("آخرین IP ورود"),
        null=True,
        blank=True,
    )

    # ─── Manager ───
    objects = UserManager()

    # ─── تنظیمات احراز هویت ───
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.phone

    # ═══════════════════════════════════════════════════════════
    #  Properties
    # ═══════════════════════════════════════════════════════════

    @property
    def is_customer(self) -> bool:
        """آیا مشتریه؟"""
        return self.role == Role.CUSTOMER

    @property
    def is_business_owner(self) -> bool:
        """آیا صاحب کسب‌وکاره؟"""
        return self.role == Role.BUSINESS_OWNER

    @property
    def is_platform_admin(self) -> bool:
        """آیا مدیر پلتفرمه؟"""
        return self.role == Role.ADMIN

    @property
    def display_name(self) -> str:
        """
        نام نمایشی کاربر.

        اول تلاش می‌کنه از پروفایل مشتری بخونه،
        بعد از کسب‌وکار، در نهایت phone.
        """
        # ─── مشتری ───
        profile = getattr(self, "customer_profile", None)
        if profile and profile.full_name:
            return profile.full_name

        # ─── کسب‌وکار ───
        business = getattr(self, "business", None)
        if business and business.name:
            return business.name

        return self.phone

    @property
    def avatar_url(self) -> str | None:
        """URL آواتار (اگه وجود داشته باشه)."""
        business = getattr(self, "business", None)
        if business and business.avatar:
            return business.avatar.url
        return None


# ═══════════════════════════════════════════════════════════════
#  CustomerProfile
# ═══════════════════════════════════════════════════════════════


class CustomerProfile(TimeStampedModel):
    """
    پروفایل مشتری.

    OneToOne با User که role=CUSTOMER داره.
    وقتی کاربر اولین بار به‌عنوان مشتری ثبت‌نام می‌کنه،
    این پروفایل خودکار ساخته میشه (با signal).

    ─── نکته: ───
    hide_ads_banner برای بستن بنر «کسب‌وکار بشو» استفاده میشه.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        verbose_name=_("کاربر"),
        primary_key=True,
    )
    full_name = models.CharField(
        _("نام کامل"),
        max_length=100,
        blank=True,
    )
    hide_ads_banner = models.BooleanField(
        _("مخفی کردن بنر تبلیغاتی"),
        default=False,
    )
    notes = models.TextField(
        _("یادداشت"),
        blank=True,
        help_text=_("یادداشت‌های داخلی (اختیاری)"),
    )

    class Meta:
        verbose_name = _("پروفایل مشتری")
        verbose_name_plural = _("پروفایل‌های مشتری")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.phone} — {self.full_name or 'بدون نام'}"


# ═══════════════════════════════════════════════════════════════
#  BusinessOwnerProfile
# ═══════════════════════════════════════════════════════════════


class BusinessOwnerProfile(TimeStampedModel):
    """
    پروفایل صاحب کسب‌وکار.

    OneToOne با User که role=BUSINESS_OWNER داره.

    ─── نکته: ───
    business (ForeignKey به Business) از سمت Business تعریف شده
    (چون Business به User نیاز داره، و یه circular dependency
    اجتناب‌ناپذیره — با string reference حلش کردیم).
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="business_owner_profile",
        verbose_name=_("کاربر"),
        primary_key=True,
    )
    national_id = models.CharField(
        _("کد ملی"),
        max_length=10,
        blank=True,
        help_text=_("برای احراز هویت (اختیاری)"),
    )

    class Meta:
        verbose_name = _("پروفایل صاحب کسب‌وکار")
        verbose_name_plural = _("پروفایل‌های صاحب کسب‌وکار")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.phone} — {self.user.display_name}"


# ═══════════════════════════════════════════════════════════════
#  OTPCode
# ═══════════════════════════════════════════════════════════════


class OTPCode(models.Model):
    """
    کد یک‌بارمصرف برای ورود.

    ─── نکته امنیتی: ───
    کدها هش نمی‌شن چون:
    1. عمرشون ۲ دقیقه‌ست
    2. یک‌بارمصرفن
    3. rate limit داریم

    اگه بعداً خواستی هش کنی، از `hashers.make_password` استفاده کن.
    """

    phone = models.CharField(
        _("شماره موبایل"),
        max_length=11,
        db_index=True,
    )
    code = models.CharField(
        _("کد"),
        max_length=10,
    )
    is_used = models.BooleanField(
        _("استفاده شده"),
        default=False,
        db_index=True,
    )
    attempts = models.PositiveSmallIntegerField(
        _("تعداد تلاش‌ها"),
        default=0,
    )
    created_at = models.DateTimeField(
        _("تاریخ ایجاد"),
        auto_now_add=True,
        db_index=True,
    )
    expires_at = models.DateTimeField(
        _("تاریخ انقضا"),
        db_index=True,
    )
    used_at = models.DateTimeField(
        _("تاریخ استفاده"),
        null=True,
        blank=True,
    )
    ip_address = models.GenericIPAddressField(
        _("IP"),
        null=True,
        blank=True,
    )
    user_agent = models.CharField(
        _("User-Agent"),
        max_length=255,
        blank=True,
    )

    objects = OTPCodeManager()

    class Meta:
        verbose_name = _("کد یک‌بارمصرف")
        verbose_name_plural = _("کدهای یک‌بارمصرف")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "code", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.phone} — {self.code}"

    # ═══════════════════════════════════════════════════════════
    #  Properties
    # ═══════════════════════════════════════════════════════════

    @property
    def is_expired(self) -> bool:
        """آیا منقضی شده؟"""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """آیا هنوز قابل استفاده‌ست؟"""
        return not self.is_used and not self.is_expired

    @property
    def seconds_until_expiry(self) -> int:
        """چند ثانیه تا انقضا مونده (ممکنه منفی بشه)."""
        delta = self.expires_at - timezone.now()
        return int(delta.total_seconds())

    # ═══════════════════════════════════════════════════════════
    #  Methods
    # ═══════════════════════════════════════════════════════════

    def mark_as_used(self) -> None:
        """علامت‌گذاری به‌عنوان استفاده‌شده."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

    def increment_attempts(self) -> int:
        """افزایش تعداد تلاش‌ها و برگردوندن مقدار جدید."""
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return self.attempts

    @classmethod
    def cleanup_expired(cls, hours: int = 24) -> int:
        """حذف OTP های منقضی‌شده‌ی قدیمی."""
        cutoff = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(expires_at__lt=cutoff).delete()[0]