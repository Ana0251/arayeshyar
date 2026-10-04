"""
مدل‌های اپ business.

شامل:
1.  TargetAudience       — مخاطب (آقایان/بانوان/هردو/کودکان)
2.  ActivityType         — نوع فعالیت (آرایشگر، سالن، ناخن‌کار، ...)
3.  Plan                 — پلن اشتراک (قابل مدیریت از ادمین)
4.  Business             — کسب‌وکار
5.  Staff                — کارمند
6.  Station              — ایستگاه (اتاق)
7.  Service              — خدمت
8.  WorkingHours         — برنامه هفتگی
9.  DayOff               — روز تعطیل
10. SpecialWorkingHours  — ساعت خاص
11. Break                — وقفه استراحت
12. ProfileChangeRequest — درخواست تغییر حساس
13. Payment              — پرداخت
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
#  ۳. Plan (پلن اشتراک)
# ═══════════════════════════════════════════════════════════════


class Plan(TimeStampedModel):
    """
    پلن اشتراک (قابل مدیریت از ادمین).

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
        help_text=_("اگه True، امکانات pro (یادآور، لیست انتظار، ...) فعالن."),
    )

    class Meta:
        verbose_name = _("پلن")
        verbose_name_plural = _("پلن‌ها")
        ordering = ["order", "price"]

    def __str__(self) -> str:
        return f"{self.icon} {self.name}"

    @property
    def features_count(self) -> int:
        """تعداد ویژگی‌ها."""
        return len(self.features) if isinstance(self.features, list) else 0


# ═══════════════════════════════════════════════════════════════
#  ۴. Business
# ═══════════════════════════════════════════════════════════════


class Business(TimeStampedModel):
    """کسب‌وکار — آرایشگر، سالن، ناخن‌کار، ماساژور، تتو کار، ..."""

    # ─── مالکیت ───
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="business",
        verbose_name=_("صاحب کسب‌وکار"),
        limit_choices_to={"role": Role.BUSINESS_OWNER},
    )

    # ─── نوع کسب‌وکار ───
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

    # ─── اطلاعات پایه ───
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

    # ─── تصاویر ───
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

    # ─── وضعیت تأیید ───
    is_active = models.BooleanField(_("تأیید شده"), default=False, db_index=True)
    is_rejected = models.BooleanField(_("رد شده"), default=False)
    rejection_reason = models.TextField(_("دلیل رد"), blank=True)

    # ─── پلن ───
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="businesses",
        verbose_name=_("پلن فعلی"),
    )
    plan_expires_at = models.DateField(_("تاریخ انقضای پلن"), null=True, blank=True)

    # ─── تنظیمات ───
    auto_confirm = models.BooleanField(_("تأیید خودکار نوبت‌ها"), default=False)

    # ─── Manager ───
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

    # ═══════════════════════════════════════════════════════════
    #  Save
    # ═══════════════════════════════════════════════════════════

    def save(self, *args, **kwargs) -> None:
        """ساخت خودکار slug اگه نداشت."""
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        """ساخت slug یکتا از name."""
        base_slug = slugify(self.name, allow_unicode=True) or "business"
        slug = base_slug
        counter = 1

        while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"

        return slug

    # ═══════════════════════════════════════════════════════════
    #  Properties — وضعیت
    # ═══════════════════════════════════════════════════════════

    @property
    def is_pending(self) -> bool:
        return not self.is_active and not self.is_rejected

    @property
    def is_approved(self) -> bool:
        return self.is_active and not self.is_rejected

    @property
    def has_pro_features(self) -> bool:
        return self.plan.has_pro_features and self.is_plan_active

    @property
    def is_plan_active(self) -> bool:
        """
        آیا پلن فعلی معتبره؟

        ─── منطق: ───
        اگه plan_expires_at داره: تاریخ رو چک کن.
        اگه نداره: False (چون هر پلنی باید تاریخ داشته باشه).
        """
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
    - صاحب کسب‌وکار هم یه Staff هست (is_owner=True، خودکار ساخته میشه)
    - خدمت می‌تونه چند Staff داشته باشه (M2M)
    - اتاق هم می‌تونه چند Staff داشته باشه (M2M، اختیاری)
    - توی کسب‌وکار شخصی، فقط یه Staff هست (صاحب)
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
    - staff_members: کارمندهای این اتاق (اختیاری)
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="stations",
        verbose_name=_("کسب‌وکار"),
    )
    staff_members = models.ManyToManyField(
        Staff,
        related_name="stations",
        blank=True,
        verbose_name=_("کارمندها"),
        help_text=_("کارمندهایی که توی این ایستگاه کار می‌کنن (اختیاری)"),
    )
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
#  ۷. Service
# ═══════════════════════════════════════════════════════════════


class Service(TimeStampedModel):
    """
    خدمت.

    ─── نکته: ───
    - station اجباریه (هر خدمت توی یه ایستگاه)
    - staff_members: مسئول‌های این خدمت (چند به چند)
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
    staff_members = models.ManyToManyField(
        Staff,
        related_name="services",
        blank=True,
        verbose_name=_("مسئول‌ها"),
        help_text=_("کارمندهایی که این خدمت رو انجام میدن"),
    )
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
        return self.staff_members.filter(is_active=True).count()


# ═══════════════════════════════════════════════════════════════
#  ۸. WorkingHours
# ═══════════════════════════════════════════════════════════════


class WorkingHours(TimeStampedModel):
    """برنامه هفتگی کسب‌وکار."""

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
#  ۹. DayOff
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
#  ۱۰. SpecialWorkingHours
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

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_("ساعت پایان باید بعد از ساعت شروع باشه."))


# ═══════════════════════════════════════════════════════════════
#  ۱۱. Break
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

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_("ساعت پایان باید بعد از ساعت شروع باشه."))


# ═══════════════════════════════════════════════════════════════
#  ۱۲. ProfileChangeRequest
# ═══════════════════════════════════════════════════════════════


class ProfileChangeRequest(TimeStampedModel):
    """درخواست تغییر فیلدهای حساس پروفایل."""

    # ─── Generic FK ───
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("نوع مدل"),
    )
    object_id = models.PositiveIntegerField(_("شناسه"))
    content_object = GenericForeignKey("content_type", "object_id")

    # ─── کوت (برای دسترسی سریع) ───
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="change_requests",
        verbose_name=_("کسب‌وکار"),
        null=True,
        blank=True,
    )

    # ─── فیلد مورد تغییر ───
    field_name = models.CharField(
        _("فیلد مورد تغییر"),
        max_length=30,
        choices=ProfileField.choices,
    )

    # ─── مقدار قدیم ───
    old_value_text = models.TextField(_("مقدار قبلی (متنی)"), blank=True)

    # ─── مقدار جدید ───
    new_value_text = models.TextField(_("مقدار جدید (متنی)"), blank=True)
    new_value_file = models.FileField(
        _("فایل جدید"),
        upload_to=UPLOAD_PATHS["change_request"],
        blank=True,
        null=True,
    )

    # ─── وضعیت ───
    status = models.CharField(
        _("وضعیت"),
        max_length=10,
        choices=ChangeRequestStatus.choices,
        default=ChangeRequestStatus.PENDING,
        db_index=True,
    )
    rejection_reason = models.TextField(_("دلیل رد"), blank=True)

    # ─── تاریخ بررسی ───
    reviewed_at = models.DateTimeField(_("تاریخ بررسی"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_changes",
        verbose_name=_("بررسی‌کننده"),
    )

    # ─── Manager ───
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
        """تأیید و اعمال درخواست."""
        from .services.changes import apply_change_request

        apply_change_request(self)

        self.status = ChangeRequestStatus.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.save(update_fields=["status", "reviewed_at", "reviewed_by"])

    def reject(self, reason: str, reviewed_by: User | None = None) -> None:
        """رد درخواست با دلیل."""
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
#  ۱۳. Payment
# ═══════════════════════════════════════════════════════════════


class Payment(TimeStampedModel):
    """
    پرداخت برای خرید پلن.

    ─── جریان: ───
    1. کسب‌وکار پلن رو انتخاب می‌کنه
    2. مبلغ رو کارت به کارت می‌کنه
    3. رسید رو آپلود می‌کنه
    4. ادمین تأیید/رد می‌کنه
    5. بعد از تأیید → پلن فعال میشه
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("کسب‌وکار"),
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name=_("پلن"),
    )
    amount = models.PositiveIntegerField(
        _("مبلغ (تومان)"),
    )
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

    # ─── رسید ───
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
        help_text=_("شماره پیگیری تراکنش"),
    )

    # ─── یادداشت ───
    customer_note = models.TextField(
        _("یادداشت مشتری"),
        blank=True,
        max_length=500,
    )
    admin_note = models.TextField(
        _("یادداشت ادمین"),
        blank=True,
        max_length=500,
    )

    # ─── تاریخ بررسی ───
    reviewed_at = models.DateTimeField(
        _("تاریخ بررسی"),
        null=True,
        blank=True,
    )
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
        """
        تأیید پرداخت → فعال‌سازی پلن.

        ─── منطق: ───
        1. اگه پلن فعلی هنوز معتبره → اضافه کن به تاریخ انقضا
        2. وگرنه → از امروز شروع کن
        """
        business = self.business
        today = timezone.localdate()
        duration = self.plan.duration_days

        # ─── محاسبه‌ی تاریخ انقضای جدید ───
        if (
            business.plan_id == self.plan_id
            and business.plan_expires_at
            and business.plan_expires_at >= today
        ):
            # ─── تمدید: از تاریخ انقضای فعلی ───
            new_expiry = business.plan_expires_at + timedelta(days=duration)
        else:
            # ─── پلن جدید: از امروز ───
            new_expiry = today + timedelta(days=duration)

        # ─── آپدیت Business ───
        business.plan = self.plan
        business.plan_expires_at = new_expiry
        business.save(update_fields=["plan", "plan_expires_at"])

        # ─── آپدیت Payment ───
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
        """رد پرداخت."""
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