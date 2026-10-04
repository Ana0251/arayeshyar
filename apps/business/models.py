"""
مدل‌های اپ business.

شامل:
1.  TargetAudience       — مخاطب
2.  ActivityType         — نوع فعالیت
3.  Plan                 — پلن اشتراک (قابل مدیریت)
4.  Business             — کسب‌وکار
5.  Staff                — کارمند
6.  Station              — ایستگاه (اتاق)
7.  StaffSchedule        — شیفت کارمند در اتاق
8.  Service              — خدمت
9.  StaffService         — خدمات per-staff
10. WorkingHours         — برنامه هفتگی (فقط شخصی)
11. DayOff               — روز تعطیل
12. SpecialWorkingHours  — ساعت خاص
13. Break                — وقفه
14. ProfileChangeRequest — درخواست تغییر
15. Payment              — پرداخت
"""

from datetime import timedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.core.models import TimeStampedModel

from .constants import (
    UPLOAD_PATHS,
    ChangeRequestStatus,
    PaymentMethod,
    PaymentStatus,
    ProfileField,
    Weekday,
)
from .managers import (
    BusinessManager,
    ProfileChangeRequestManager,
)
from .validators import validate_image


# ═══════════════════════════════════════════════════════════════
#  ۱. TargetAudience
# ═══════════════════════════════════════════════════════════════


class TargetAudience(TimeStampedModel):
    """مخاطب — خدمات به چه کسی ارائه میشه؟"""

    slug = models.SlugField(_("شناسه"), max_length=50, unique=True)
    name = models.CharField(_("نام"), max_length=50)
    icon = models.CharField(_("آیکون"), max_length=10, blank=True)
    order = models.PositiveIntegerField(_("ترتیب نمایش"), default=0)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("مخاطب")
        verbose_name_plural = _("مخاطبین")
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.icon} {self.name}".strip()


# ═══════════════════════════════════════════════════════════════
#  ۲. ActivityType
# ═══════════════════════════════════════════════════════════════


class ActivityType(TimeStampedModel):
    """نوع فعالیت — سالن زیبایی، آرایشگر، ناخن‌کار، ..."""

    slug = models.SlugField(_("شناسه"), max_length=100, unique=True)
    name = models.CharField(_("نام"), max_length=100)
    icon = models.CharField(_("آیکون"), max_length=10, blank=True)
    is_salon = models.BooleanField(
        _("مخصوص سالن"),
        default=False,
        help_text=_("آیا این نوع فعالیت مخصوص سالن‌هاست؟"),
    )
    order = models.PositiveIntegerField(_("ترتیب نمایش"), default=0)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("نوع فعالیت")
        verbose_name_plural = _("انواع فعالیت")
        ordering = ["is_salon", "order", "id"]

    def __str__(self) -> str:
        prefix = "🏢" if self.is_salon else "💁"
        return f"{prefix} {self.icon} {self.name}".strip()


# ═══════════════════════════════════════════════════════════════
#  ۳. Plan (پلن اشتراک — قابل مدیریت از ادمین)
# ═══════════════════════════════════════════════════════════════


class Plan(TimeStampedModel):
    """
    پلن اشتراک.

    ─── چرا مدل؟ ───
    ادمین بتونه:
    - پلن جدید بسازه
    - قیمت‌ها رو عوض کنه
    - ویژگی‌ها رو کم/زیاد کنه
    - ترتیب نمایش رو تنظیم کنه
    """

    slug = models.SlugField(
        _("شناسه"),
        max_length=50,
        unique=True,
        help_text=_("مثلاً: trial, basic, pro"),
    )
    name = models.CharField(
        _("نام"),
        max_length=50,
        help_text=_("مثلاً: پلن پایه"),
    )
    icon = models.CharField(
        _("آیکون"),
        max_length=10,
        blank=True,
        default="⭐",
        help_text=_("مثلاً: 🎁 ⭐ 💎"),
    )
    description = models.TextField(
        _("توضیحات"),
        blank=True,
        max_length=500,
    )
    price = models.PositiveIntegerField(
        _("قیمت (تومان)"),
        default=0,
    )
    duration_days = models.PositiveIntegerField(
        _("مدت (روز)"),
        default=30,
    )
    features = models.JSONField(
        _("ویژگی‌ها"),
        default=list,
        blank=True,
        help_text=_('لیست ویژگی‌ها — مثال: ["نوبت‌دهی آنلاین", "QR Code"]'),
    )
    order = models.PositiveIntegerField(
        _("ترتیب نمایش"),
        default=0,
    )
    is_active = models.BooleanField(
        _("فعال"),
        default=True,
        help_text=_("اگه غیرفعال باشه، توی لیست خرید نشون داده نمیشه."),
    )
    is_paid = models.BooleanField(
        _("پولی"),
        default=True,
        help_text=_("پلن‌های رایگان (مثل trial) این فیلد رو False می‌کنن."),
    )
    has_pro_features = models.BooleanField(
        _("ویژگی‌های ویژه"),
        default=False,
        help_text=_("اگه True، امکانات pro فعالن."),
    )

    class Meta:
        verbose_name = _("پلن")
        verbose_name_plural = _("پلن‌ها")
        ordering = ["order", "price"]

    def __str__(self) -> str:
        return f"{self.icon} {self.name}"

    @property
    def features_count(self) -> int:
        return len(self.features) if isinstance(self.features, list) else 0


# ═══════════════════════════════════════════════════════════════
#  ۴. Business
# ═══════════════════════════════════════════════════════════════


class Business(TimeStampedModel):
    """کسب‌وکار — آرایشگر، سالن، ناخن‌کار، ..."""

    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="business",
        verbose_name=_("صاحب کسب‌وکار"),
        limit_choices_to={"role": Role.BUSINESS_OWNER},
    )
    target_audience = models.ForeignKey(
        TargetAudience,
        on_delete=models.PROTECT,
        related_name="businesses",
        verbose_name=_("مخاطب"),
    )
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.PROTECT,
        related_name="businesses",
        verbose_name=_("نوع فعالیت"),
    )
    is_salon = models.BooleanField(_("سالن داره؟"), default=False, db_index=True)

    name = models.CharField(_("نام"), max_length=100)
    slug = models.SlugField(
        _("شناسه لینک"),
        max_length=150,
        unique=True,
        blank=True,
        db_index=True,
    )
    owner_name = models.CharField(_("اسم صاحب کسب‌وکار"), max_length=100, blank=True)
    landline = models.CharField(_("تلفن ثابت"), max_length=15, blank=True)
    region = models.CharField(_("منطقه"), max_length=100, db_index=True)
    address = models.CharField(_("آدرس"), max_length=255)
    bio = models.TextField(_("درباره ما"), max_length=500, blank=True)

    avatar = models.ImageField(
        _("عکس پروفایل"),
        upload_to=UPLOAD_PATHS["avatar"],
        blank=True,
        null=True,
        validators=[validate_image],
    )
    business_license = models.ImageField(
        _("عکس پروانه کسب"),
        upload_to=UPLOAD_PATHS["business_license"],
        blank=True,
        null=True,
        validators=[validate_image],
    )
    entrance_photo = models.ImageField(
        _("عکس ورودی و تابلو"),
        upload_to=UPLOAD_PATHS["entrance_photo"],
        blank=True,
        null=True,
        validators=[validate_image],
    )

    is_active = models.BooleanField(_("تأیید شده"), default=False, db_index=True)
    is_rejected = models.BooleanField(_("رد شده"), default=False)
    rejection_reason = models.TextField(_("دلیل رد"), blank=True)

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="businesses",
        verbose_name=_("پلن"),
    )
    plan_expires_at = models.DateField(_("تاریخ انقضای پلن"), null=True, blank=True)

    auto_confirm = models.BooleanField(_("تأیید خودکار نوبت‌ها"), default=False)

    objects = BusinessManager()

    class Meta:
        verbose_name = _("کسب‌وکار")
        verbose_name_plural = _("کسب‌وکارها")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "region"]),
            models.Index(fields=["is_active", "is_salon"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        icon = "🏢" if self.is_salon else "💁"
        return f"{icon} {self.name}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        base_slug = slugify(self.name, allow_unicode=True) or "business"
        slug = base_slug
        counter = 1

        while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"

        return slug

    @property
    def is_pending(self) -> bool:
        return not self.is_active and not self.is_rejected

    @property
    def is_approved(self) -> bool:
        return self.is_active and not self.is_rejected

    @property
    def has_pro_features(self) -> bool:
        return bool(self.plan and self.plan.has_pro_features and self.is_plan_active)

    @property
    def is_plan_active(self) -> bool:
        if not self.plan_expires_at:
            return False
        return self.plan_expires_at >= timezone.localdate()

    @property
    def plan_days_left(self) -> int | None:
        if not self.plan_expires_at:
            return None
        delta = self.plan_expires_at - timezone.localdate()
        return delta.days

    @property
    def services_count(self) -> int:
        return self.services.filter(is_active=True).count()

    @property
    def stations_count(self) -> int:
        return self.stations.filter(is_active=True).count()

    @property
    def staff_count(self) -> int:
        return self.staff.filter(is_active=True).count()

    @property
    def pending_changes_count(self) -> int:
        return self.change_requests.filter(
            status=ChangeRequestStatus.PENDING
        ).count()

    @property
    def has_pending_changes(self) -> bool:
        return self.pending_changes_count > 0

    @property
    def public_url(self) -> str:
        return f"/b/{self.slug}/"


# ═══════════════════════════════════════════════════════════════
#  ۵. Staff
# ═══════════════════════════════════════════════════════════════


class Staff(TimeStampedModel):
    """
    کارمند کسب‌وکار.

    ─── نکته: ───
    - صاحب کسب‌وکار هم یه Staff هست (is_owner=True)
    - خدمت از طریق StaffService به Staff وصل میشه
    - شیفت از طریق StaffSchedule مدیریت میشه
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="staff",
        verbose_name=_("کسب‌وکار"),
    )
    name = models.CharField(_("نام"), max_length=100)
    phone = models.CharField(_("شماره موبایل"), max_length=15, blank=True)
    avatar = models.ImageField(
        _("عکس"),
        upload_to="staff/avatars/",
        blank=True,
        null=True,
        validators=[validate_image],
    )
    bio = models.TextField(_("درباره"), max_length=300, blank=True)
    is_owner = models.BooleanField(_("صاحب کسب‌وکار"), default=False)
    is_active = models.BooleanField(_("فعال"), default=True)
    order = models.PositiveIntegerField(_("ترتیب"), default=0)

    class Meta:
        verbose_name = _("کارمند")
        verbose_name_plural = _("کارمندها")
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["business"],
                condition=models.Q(is_owner=True),
                name="unique_owner_per_business",
            ),
        ]

    def __str__(self) -> str:
        suffix = " (صاحب)" if self.is_owner else ""
        return f"{self.name}{suffix}"


# ═══════════════════════════════════════════════════════════════
#  ۶. Station
# ═══════════════════════════════════════════════════════════════


class Station(TimeStampedModel):
    """
    ایستگاه توی یه کسب‌وکار.

    ─── نکته: ───
    - برای سالن: اتاق (اتاق رنگ، اتاق ناخن، ...)
    - برای شخصی: یه Station خودکار («محل کار»)
    - کارمندها از طریق StaffSchedule و StaffService مدیریت میشن
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="stations",
        verbose_name=_("کسب‌وکار"),
    )
    # ─── ❌ staff_members حذف شد ───
    name = models.CharField(_("نام ایستگاه"), max_length=100)
    order = models.PositiveIntegerField(_("ترتیب"), default=0)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("ایستگاه")
        verbose_name_plural = _("ایستگاه‌ها")
        ordering = ["order", "id"]
        unique_together = [("business", "name")]

    def __str__(self) -> str:
        return self.name

    @property
    def services_count(self) -> int:
        return self.services.filter(is_active=True).count()


# ═══════════════════════════════════════════════════════════════
#  ۷. StaffSchedule (شیفت کارمند در اتاق)
# ═══════════════════════════════════════════════════════════════


class StaffSchedule(TimeStampedModel):
    """
    شیفت کاری کارمند توی یه اتاق.

    ─── نکته: ───
    یه کارمند می‌تونه توی چند اتاق شیفت داشته باشه.
    توی هر اتاق، ساعت کاری می‌تونه متفاوت باشه.
    """

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name=_("کارمند"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="staff_schedules",
        verbose_name=_("اتاق"),
    )
    weekday = models.IntegerField(
        _("روز هفته"),
        choices=Weekday.choices,
    )
    start_time = models.TimeField(_("ساعت شروع"))
    end_time = models.TimeField(_("ساعت پایان"))
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("شیفت کارمند")
        verbose_name_plural = _("شیفت‌های کارمند")
        ordering = ["station", "weekday", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["staff", "station", "weekday", "start_time"],
                name="unique_staff_station_weekday_start",
            ),
        ]
        indexes = [
            models.Index(fields=["station", "weekday"]),
            models.Index(fields=["staff", "weekday"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.staff.name} @ {self.station.name} — "
            f"{self.get_weekday_display()} {self.start_time}-{self.end_time}"
        )

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_("ساعت پایان باید بعد از ساعت شروع باشه."))

    @property
    def duration_minutes(self) -> int:
        if not (self.start_time and self.end_time):
            return 0
        from datetime import datetime

        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:
            end += timedelta(days=1)
        return int((end - start).total_seconds() / 60)


# ═══════════════════════════════════════════════════════════════
#  ۸. Service
# ═══════════════════════════════════════════════════════════════


class Service(TimeStampedModel):
    """
    خدمت.

    ─── نکته: ───
    - station اجباریه
    - مسئول‌ها از طریق StaffService (نه M2M)
    - duration برای محاسبه اسلات‌ها
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("کسب‌وکار"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="services",
        verbose_name=_("ایستگاه"),
    )
    # ─── ❌ staff_members حذف شد ───
    name = models.CharField(_("نام خدمت"), max_length=100)
    duration = models.PositiveIntegerField(
        _("مدت (دقیقه)"),
        default=30,
        validators=[MinValueValidator(5)],
    )
    price = models.PositiveIntegerField(_("قیمت (تومان)"), default=0)
    is_active = models.BooleanField(_("فعال"), default=True)
    order = models.PositiveIntegerField(_("ترتیب"), default=0)

    class Meta:
        verbose_name = _("خدمت")
        verbose_name_plural = _("خدمات")
        ordering = ["order", "name"]
        unique_together = [("business", "station", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.duration} دقیقه)"

    @property
    def duration_delta(self) -> timedelta:
        return timedelta(minutes=self.duration)

    @property
    def price_display(self) -> str:
        if not self.price:
            return "—"
        return f"{self.price:,} تومان"

    @property
    def staff_count(self) -> int:
        """تعداد کارمندهای فعال (از StaffService)."""
        return self.staff_services.filter(
            is_active=True,
            staff__is_active=True,
        ).count()


# ═══════════════════════════════════════════════════════════════
#  ۹. StaffService (خدمات per-staff)
# ═══════════════════════════════════════════════════════════════


class StaffService(TimeStampedModel):
    """
    خدمتی که یه کارمند توی یه اتاق ارائه می‌ده.

    ─── نکته: ───
    - یه کارمند می‌تونه توی چند اتاق، خدمات مختلف بده
    - قیمت per-staff per-station می‌تونه متفاوت باشه
    - اگه price=0 باشه، از Service.price استفاده میشه
    """

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="staff_services",
        verbose_name=_("کارمند"),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="staff_services",
        verbose_name=_("خدمت"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="staff_services",
        verbose_name=_("اتاق"),
    )
    price = models.PositiveIntegerField(
        _("قیمت اختصاصی (تومان)"),
        default=0,
        help_text=_("اگه ۰ باشه، از قیمت پیش‌فرض خدمت استفاده میشه."),
    )
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("خدمت کارمند")
        verbose_name_plural = _("خدمات کارمند")
        ordering = ["station", "service", "staff"]
        constraints = [
            models.UniqueConstraint(
                fields=["staff", "service", "station"],
                name="unique_staff_service_station",
            ),
        ]
        indexes = [
            models.Index(fields=["service", "is_active"]),
            models.Index(fields=["staff", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.staff.name} — {self.service.name} @ {self.station.name}"

    @property
    def effective_price(self) -> int:
        if self.price > 0:
            return self.price
        return self.service.price

    @property
    def effective_duration(self) -> int:
        return self.service.duration


# ═══════════════════════════════════════════════════════════════
#  ۱۰. WorkingHours (فقط برای کسب‌وکار شخصی)
# ═══════════════════════════════════════════════════════════════


class WorkingHours(TimeStampedModel):
    """برنامه هفتگی کسب‌وکار (فقط برای شخصی)."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="working_hours",
        verbose_name=_("کسب‌وکار"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="working_hours",
        verbose_name=_("ایستگاه"),
    )
    weekday = models.IntegerField(_("روز هفته"), choices=Weekday.choices)
    start_time = models.TimeField(_("ساعت شروع"))
    end_time = models.TimeField(_("ساعت پایان"))
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("برنامه هفتگی")
        verbose_name_plural = _("برنامه‌های هفتگی")
        ordering = ["weekday"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "station", "weekday"],
                condition=models.Q(station__isnull=False),
                name="unique_working_hours_with_station",
            ),
            models.UniqueConstraint(
                fields=["business", "weekday"],
                condition=models.Q(station__isnull=True),
                name="unique_working_hours_no_station",
            ),
        ]

    def __str__(self) -> str:
        target = self.station.name if self.station else self.business.name
        return f"{target} — {self.get_weekday_display()} ({self.start_time} تا {self.end_time})"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_("ساعت پایان باید بعد از ساعت شروع باشه."))


# ═══════════════════════════════════════════════════════════════
#  ۱۱. DayOff
# ═══════════════════════════════════════════════════════════════


class DayOff(TimeStampedModel):
    """روز تعطیل خاص."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="days_off",
        verbose_name=_("کسب‌وکار"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="days_off",
        verbose_name=_("ایستگاه"),
    )
    date = models.DateField(_("تاریخ تعطیلی"), db_index=True)
    reason = models.CharField(_("دلیل"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("روز تعطیل")
        verbose_name_plural = _("روزهای تعطیل")
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "station", "date"],
                condition=models.Q(station__isnull=False),
                name="unique_day_off_with_station",
            ),
            models.UniqueConstraint(
                fields=["business", "date"],
                condition=models.Q(station__isnull=True),
                name="unique_day_off_no_station",
            ),
        ]

    def __str__(self) -> str:
        target = self.station.name if self.station else self.business.name
        return f"{target} — {self.date}"


# ═══════════════════════════════════════════════════════════════
#  ۱۲. SpecialWorkingHours
# ═══════════════════════════════════════════════════════════════


class SpecialWorkingHours(TimeStampedModel):
    """ساعت کاری خاص برای یه تاریخ مشخص."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="special_hours",
        verbose_name=_("کسب‌وکار"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="special_hours",
        verbose_name=_("ایستگاه"),
    )
    date = models.DateField(_("تاریخ"), db_index=True)
    start_time = models.TimeField(_("ساعت شروع"))
    end_time = models.TimeField(_("ساعت پایان"))
    note = models.CharField(_("یادداشت"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("ساعت کاری خاص")
        verbose_name_plural = _("ساعت‌های کاری خاص")
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "station", "date"],
                condition=models.Q(station__isnull=False),
                name="unique_special_hours_with_station",
            ),
            models.UniqueConstraint(
                fields=["business", "date"],
                condition=models.Q(station__isnull=True),
                name="unique_special_hours_no_station",
            ),
        ]

    def __str__(self) -> str:
        target = self.station.name if self.station else self.business.name
        return f"{target} — {self.date}"


# ═══════════════════════════════════════════════════════════════
#  ۱۳. Break
# ═══════════════════════════════════════════════════════════════


class Break(TimeStampedModel):
    """وقفه استراحت."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="breaks",
        verbose_name=_("کسب‌وکار"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="breaks",
        verbose_name=_("ایستگاه"),
    )
    start_time = models.TimeField(_("از ساعت"))
    end_time = models.TimeField(_("تا ساعت"))
    label = models.CharField(_("عنوان"), max_length=100, blank=True)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("وقفه استراحت")
        verbose_name_plural = _("وقفه‌های استراحت")
        ordering = ["start_time"]

    def __str__(self) -> str:
        target = self.station.name if self.station else self.business.name
        return f"{target} — {self.start_time} تا {self.end_time}"


# ═══════════════════════════════════════════════════════════════
#  ۱۴. ProfileChangeRequest
# ═══════════════════════════════════════════════════════════════


class ProfileChangeRequest(TimeStampedModel):
    """درخواست تغییر فیلدهای حساس پروفایل."""

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("نوع مدل"),
    )
    object_id = models.PositiveIntegerField(_("شناسه"))
    content_object = GenericForeignKey("content_type", "object_id")

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="change_requests",
        verbose_name=_("کسب‌وکار"),
        null=True,
        blank=True,
    )

    field_name = models.CharField(
        _("فیلد مورد تغییر"),
        max_length=30,
        choices=ProfileField.choices,
    )

    old_value_text = models.TextField(_("مقدار قبلی (متنی)"), blank=True)
    new_value_text = models.TextField(_("مقدار جدید (متنی)"), blank=True)
    new_value_file = models.FileField(
        _("فایل جدید"),
        upload_to=UPLOAD_PATHS["change_request"],
        blank=True,
        null=True,
    )

    status = models.CharField(
        _("وضعیت"),
        max_length=10,
        choices=ChangeRequestStatus.choices,
        default=ChangeRequestStatus.PENDING,
        db_index=True,
    )
    rejection_reason = models.TextField(_("دلیل رد"), blank=True)

    reviewed_at = models.DateTimeField(_("تاریخ بررسی"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_changes",
        verbose_name=_("بررسی‌کننده"),
    )

    objects = ProfileChangeRequestManager()

    class Meta:
        verbose_name = _("درخواست تغییر")
        verbose_name_plural = _("درخواست‌های تغییر")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.business.name if self.business else '—'} — {self.get_field_name_display()}"

    @property
    def is_file_field(self) -> bool:
        from .constants import FILE_FIELDS

        return self.field_name in FILE_FIELDS

    @property
    def is_pending(self) -> bool:
        return self.status == ChangeRequestStatus.PENDING

    def approve(self, reviewed_by: User | None = None) -> None:
        from .services.changes import apply_change_request

        apply_change_request(self)

        self.status = ChangeRequestStatus.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.save(update_fields=["status", "reviewed_at", "reviewed_by"])

    def reject(self, reason: str, reviewed_by: User | None = None) -> None:
        if self.new_value_file:
            self.new_value_file.delete(save=False)

        self.status = ChangeRequestStatus.REJECTED
        self.rejection_reason = reason
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.save(
            update_fields=[
                "status",
                "rejection_reason",
                "reviewed_at",
                "reviewed_by",
            ]
        )


# ═══════════════════════════════════════════════════════════════
#  ۱۵. Payment
# ═══════════════════════════════════════════════════════════════


class Payment(TimeStampedModel):
    """پرداخت برای خرید پلن."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("کسب‌وکار"),
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("پلن"),
    )
    amount = models.PositiveIntegerField(_("مبلغ (تومان)"))
    method = models.CharField(
        _("روش پرداخت"),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD_TO_CARD,
    )
    status = models.CharField(
        _("وضعیت"),
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )

    receipt = models.ImageField(
        _("عکس رسید"),
        upload_to="payments/receipts/",
        blank=True,
        null=True,
        validators=[validate_image],
    )
    tracking_code = models.CharField(
        _("کد پیگیری"),
        max_length=50,
        blank=True,
    )

    customer_note = models.TextField(_("یادداشت مشتری"), blank=True, max_length=500)
    admin_note = models.TextField(_("یادداشت ادمین"), blank=True, max_length=500)

    reviewed_at = models.DateTimeField(_("تاریخ بررسی"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payments",
        verbose_name=_("بررسی‌کننده"),
    )

    class Meta:
        verbose_name = _("پرداخت")
        verbose_name_plural = _("پرداخت‌ها")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        plan_name = self.plan.name if self.plan else "—"
        return f"{self.business.name} — {plan_name} — {self.amount:,} تومان"

    @property
    def is_pending(self) -> bool:
        return self.status == PaymentStatus.PENDING

    @property
    def is_approved(self) -> bool:
        return self.status == PaymentStatus.APPROVED

    def approve(self, reviewed_by: User | None = None, note: str = "") -> None:
        """تأیید پرداخت → فعال‌سازی پلن."""
        if not self.plan:
            raise ValueError("پلن تعیین نشده.")

        business = self.business
        today = timezone.localdate()
        duration = self.plan.duration_days

        if (
            business.plan
            and business.plan.pk == self.plan.pk
            and business.plan_expires_at
            and business.plan_expires_at >= today
        ):
            new_expiry = business.plan_expires_at + timedelta(days=duration)
        else:
            new_expiry = today + timedelta(days=duration)

        business.plan = self.plan
        business.plan_expires_at = new_expiry
        business.save(update_fields=["plan", "plan_expires_at"])

        self.status = PaymentStatus.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        if note:
            self.admin_note = note
        self.save(
            update_fields=[
                "status",
                "reviewed_at",
                "reviewed_by",
                "admin_note",
            ]
        )

    def reject(self, reason: str, reviewed_by: User | None = None) -> None:
        self.status = PaymentStatus.REJECTED
        self.admin_note = reason
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.save(
            update_fields=[
                "status",
                "admin_note",
                "reviewed_at",
                "reviewed_by",
            ]
        )