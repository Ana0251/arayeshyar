"""
مدل‌های اپ booking.

شامل ۳ مدل:
1. Appointment      — نوبت
2. WaitingList      — لیست انتظار
3. BlockedCustomer  — مشتری بلاک‌شده
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.business.models import Business, Service, Station
from apps.core.models import TimeStampedModel
from apps.core.utils.phone import normalize_phone

from .constants import (
    AppointmentStatus,
    WaitingStatus,
)
from .managers import (
    AppointmentManager,
    BlockedCustomerManager,
    WaitingListManager,
)


# ═══════════════════════════════════════════════════════════════
#  ۱. Appointment
# ═══════════════════════════════════════════════════════════════


class Appointment(TimeStampedModel):
    # ─── روابط ───
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("کسب‌وکار"),
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("مشتری"),
        limit_choices_to={"role": "customer"},
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        verbose_name=_("خدمت"),
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        verbose_name=_("ایستگاه"),
    )
    staff = models.ForeignKey(       # ← ← ← این خط جدید
        "business.Staff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        verbose_name=_("کارمند"),
    )
    
    

    # ─── Snapshot خدمت ───
    service_name_snapshot = models.CharField(
        _("نام خدمت (snapshot)"),
        max_length=100,
        help_text=_("در زمان رزرو ذخیره میشه"),
    )
    service_price_snapshot = models.PositiveIntegerField(
        _("قیمت خدمت (snapshot)"),
        default=0,
    )
    service_duration_snapshot = models.PositiveIntegerField(
        _("مدت خدمت (snapshot)"),
        default=30,
        help_text=_("دقیقه"),
    )

    # ─── زمان ───
    start_at = models.DateTimeField(
        _("زمان شروع"),
        db_index=True,
    )
    end_at = models.DateTimeField(
        _("زمان پایان"),
        db_index=True,
    )

    # ─── وضعیت ───
    status = models.CharField(
        _("وضعیت"),
        max_length=15,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
        db_index=True,
    )

    # ─── یادداشت ───
    customer_note = models.TextField(
        _("یادداشت مشتری"),
        blank=True,
        max_length=500,
    )
    owner_note = models.TextField(
        _("یادداشت کسب‌وکار"),
        blank=True,
        max_length=500,
    )

    # ─── چه کسی ساخت ───
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
        verbose_name=_("ایجادکننده"),
        help_text=_("اگه دستی ثبت شده، ادمین کسب‌وکار"),
    )

    # ─── وضعیت‌های تغییر ───
    confirmed_at = models.DateTimeField(
        _("زمان تأیید"),
        null=True,
        blank=True,
    )
    cancelled_at = models.DateTimeField(
        _("زمان لغو"),
        null=True,
        blank=True,
    )
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_appointments",
        verbose_name=_("لغوکننده"),
    )
    cancellation_reason = models.TextField(
        _("دلیل لغو"),
        blank=True,
        max_length=500,
    )

    # ─── Manager ───
    objects = AppointmentManager()

    class Meta:
        verbose_name = _("نوبت")
        verbose_name_plural = _("نوبت‌ها")
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["business", "start_at"]),
            models.Index(fields=["business", "status", "start_at"]),
            models.Index(fields=["customer", "start_at"]),
            models.Index(fields=["staff", "start_at"]),
            models.Index(fields=["status", "start_at"]),
            models.Index(fields=["start_at", "end_at"]),
        ]
        constraints = [
            # ═══════════════════════════════════════════════════════
            #  جلوگیری از Double Booking
            # ═══════════════════════════════════════════════════════
            #  ─── نکته: فقط برای نوبت‌های غیرلغو ───
            #  اگه نوبت لغو شده باشه، نباید جلوی رزرو جدید رو بگیره.

            # ─── ۱. هر (staff, start_at) فقط یه نوبت فعال ───
            models.UniqueConstraint(
                fields=["staff", "start_at"],
                condition=models.Q(
                    staff__isnull=False,
                    status__in=[
                        AppointmentStatus.PENDING,
                        AppointmentStatus.CONFIRMED,
                    ],
                ),
                name="unique_active_appointment_per_staff",
            ),

            # ─── ۲. هر (station, start_at) فقط یه نوبت فعال ───
            #  ─── نکته: چون station nullable نیست (SET_NULL)، بررسی می‌کنیم ───
            models.UniqueConstraint(
                fields=["station", "start_at"],
                condition=models.Q(
                    station__isnull=False,
                    status__in=[
                        AppointmentStatus.PENDING,
                        AppointmentStatus.CONFIRMED,
                    ],
                ),
                name="unique_active_appointment_per_station",
            ),
        ]

    # ═══════════════════════════════════════════════════════════
    #  Validation
    # ═══════════════════════════════════════════════════════════

    def clean(self) -> None:
        """اعتبارسنجی مدل."""
        super().clean()
         # ─── staff باید به business تعلق داشته باشه ───
        if self.staff_id and self.staff.business_id != self.business_id:
            raise ValidationError(
                _("کارمند انتخاب‌شده به این کسب‌وکار تعلق نداره.")
            )

        # ─── زمان ───
        if self.start_at and self.end_at:
            if self.end_at <= self.start_at:
                raise ValidationError(
                    _("زمان پایان باید بعد از زمان شروع باشه.")
                )

            duration_minutes = (self.end_at - self.start_at).total_seconds() / 60
            if duration_minutes < 5:
                raise ValidationError(
                    _("مدت نوبت نباید کمتر از ۵ دقیقه باشه.")
                )

        # ─── customer باید role=customer داشته باشه ───
        if self.customer_id and self.customer.role != "customer":
            raise ValidationError(
                _("کاربر انتخاب‌شده باید نقش «مشتری» داشته باشه.")
            )

        # ─── service باید به business تعلق داشته باشه ───
        if self.service_id and self.service.business_id != self.business_id:
            raise ValidationError(
                _("خدمت انتخاب‌شده به این کسب‌وکار تعلق نداره.")
            )

        # ─── station باید به business تعلق داشته باشه ───
        if self.station_id and self.station.business_id != self.business_id:
            raise ValidationError(
                _("ایستگاه انتخاب‌شده به این کسب‌وکار تعلق نداره.")
            )

        def save(self, *args, **kwargs) -> None:
            """
        محاسبه‌ی end_at اگه نبود + پر کردن snapshot ها.

        ─── منطق: ───
        - اگه start_at داره و end_at نداره → محاسبه‌ی end_at
        - اگه service_id داره و snapshot خالیه → پر کن
        - اگه end_at دستی تغییر کرده، دست نمی‌زنیم
        """
            # ─── پر کردن snapshot اگه خالیه ───
            if self.service_id and not self.service_name_snapshot:
                self.service_name_snapshot = self.service.name
                self.service_price_snapshot = self.service.price
                self.service_duration_snapshot = self.service.duration

            # ─── محاسبه‌ی end_at ───
            # فقط اگه start_at داریم و end_at نداریم (یا صفره)
            if self.start_at and not self.end_at:
                duration = self.service_duration_snapshot or 30
                self.end_at = self.start_at + timedelta(minutes=duration)

            super().save(*args, **kwargs)

    # ═══════════════════════════════════════════════════════════
    #  Properties
    # ═══════════════════════════════════════════════════════════

    @property
    def duration_minutes(self) -> int:
        """مدت نوبت به دقیقه."""
        if self.start_at and self.end_at:
            return int((self.end_at - self.start_at).total_seconds() / 60)
        return self.service_duration_snapshot

    @property
    def date(self):
        """تاریخ میلادی (برای سازگاری با کدهای قدیمی)."""
        return self.start_at.date() if self.start_at else None

    @property
    def time(self):
        """ساعت (برای سازگاری)."""
        return self.start_at.time() if self.start_at else None

    @property
    def is_pending(self) -> bool:
        return self.status == AppointmentStatus.PENDING

    @property
    def is_confirmed(self) -> bool:
        return self.status == AppointmentStatus.CONFIRMED

    @property
    def is_cancelled(self) -> bool:
        return self.status == AppointmentStatus.CANCELLED

    @property
    def is_past(self) -> bool:
        """آیا نوبت گذشته؟"""
        return self.end_at < timezone.now() if self.end_at else False

    @property
    def is_upcoming(self) -> bool:
        """آیا نوبت آینده‌ست؟"""
        return self.start_at > timezone.now() if self.start_at else False

    @property
    def can_be_cancelled(self) -> bool:
        """آیا می‌شه لغو کرد؟"""
        if self.is_cancelled or self.status == AppointmentStatus.COMPLETED:
            return False
        # حداقل ۱ ساعت قبل از نوبت
        if self.start_at:
            return self.start_at - timezone.now() > timedelta(hours=1)
        return False
        # ═══════════════════════════════════════════════════════════
    #  Properties
    # ═══════════════════════════════════════════════════════════

    @property
    def duration_minutes(self) -> int:
        """مدت نوبت به دقیقه."""
        if self.start_at and self.end_at:
            return int((self.end_at - self.start_at).total_seconds() / 60)
        return self.service_duration_snapshot

    @property
    def date(self):
        """تاریخ میلادی (برای سازگاری با کدهای قدیمی)."""
        return self.start_at.date() if self.start_at else None

    @property
    def time(self):
        """ساعت (برای سازگاری)."""
        return self.start_at.time() if self.start_at else None

    @property
    def is_pending(self) -> bool:
        return self.status == AppointmentStatus.PENDING

    @property
    def is_confirmed(self) -> bool:
        return self.status == AppointmentStatus.CONFIRMED

    @property
    def is_cancelled(self) -> bool:
        return self.status == AppointmentStatus.CANCELLED

    @property
    def is_past(self) -> bool:
        """آیا نوبت گذشته؟"""
        return self.end_at < timezone.now() if self.end_at else False

    @property
    def is_upcoming(self) -> bool:
        """آیا نوبت آینده‌ست؟"""
        return self.start_at > timezone.now() if self.start_at else False

    @property
    def can_be_cancelled(self) -> bool:
        """
        آیا می‌شه لغو کرد؟

        ─── قانون: ───
        حداقل ۱ ساعت قبل از نوبت.
        """
        if self.is_cancelled or self.status == AppointmentStatus.COMPLETED:
            return False
        # حداقل ۱ ساعت قبل از نوبت
        if self.start_at:
            return self.start_at - timezone.now() > timedelta(hours=1)
        return False

    @property
    def cancellation_deadline(self):
        """
        آخرین فرصت لغو (۱ ساعت قبل از نوبت).

        Returns:
            datetime یا None
        """
        if self.start_at:
            return self.start_at - timedelta(hours=1)
        return None

    @property
    def can_be_cancelled_reason(self) -> str:
        """
        دلیل عدم امکان لغو (اگه can_be_cancelled=False باشه).

        Returns:
            - "cancelled"   → قبلاً لغو شده
            - "completed"   → انجام شده
            - "no_start"    → زمان شروع نداره
            - "past"        → نوبت گذشته
            - "too_close"   → کمتر از ۱ ساعت مونده
            - "ok"          → می‌شه لغو کرد
        """
        if self.is_cancelled:
            return "cancelled"
        if self.status == AppointmentStatus.COMPLETED:
            return "completed"
        if not self.start_at:
            return "no_start"

        now = timezone.now()
        if self.start_at <= now:
            return "past"
        if self.start_at - now <= timedelta(hours=1):
            return "too_close"
        return "ok"
    # ═══════════════════════════════════════════════════════════
    #  Methods
    # ═══════════════════════════════════════════════════════════

    def confirm(self, by_user: User | None = None) -> None:
        """تأیید نوبت."""
        if self.status != AppointmentStatus.PENDING:
            return

        self.status = AppointmentStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_at", "updated_at"])

    def cancel(
        self,
        reason: str = "",
        by_user: User | None = None,
    ) -> None:
        """لغو نوبت."""
        if self.is_cancelled:
            return

        self.status = AppointmentStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancelled_by = by_user
        self.cancellation_reason = reason
        self.save(
            update_fields=[
                "status",
                "cancelled_at",
                "cancelled_by",
                "cancellation_reason",
                "updated_at",
            ]
        )

    def complete(self) -> None:
        """انجام شد."""
        if self.status != AppointmentStatus.CONFIRMED:
            return

        self.status = AppointmentStatus.COMPLETED
        self.save(update_fields=["status", "updated_at"])

    def mark_no_show(self) -> None:
        """مشتری نیامد."""
        if self.status != AppointmentStatus.CONFIRMED:
            return

        self.status = AppointmentStatus.NO_SHOW
        self.save(update_fields=["status", "updated_at"])


# ═══════════════════════════════════════════════════════════════
#  ۲. WaitingList
# ═══════════════════════════════════════════════════════════════


class WaitingList(TimeStampedModel):
    """
    لیست انتظار.

    وقتی مشتری برای یه تاریخ/ساعت خاص نوبت نمی‌گیره (چون پره)،
    می‌تونه توی لیست انتظار ثبت کنه. اگه ساعتی آزاد شد،
    بهش اطلاع می‌دیم.
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="waiting_list",
        verbose_name=_("کسب‌وکار"),
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="waiting_list",
        verbose_name=_("مشتری"),
        limit_choices_to={"role": Role.CUSTOMER},
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waiting_list",
        verbose_name=_("خدمت"),
    )

    # ─── Snapshot ───
    service_name_snapshot = models.CharField(
        _("نام خدمت (snapshot)"),
        max_length=100,
    )

    # ─── زمان مورد نظر ───
    date = models.DateField(
        _("تاریخ مورد نظر"),
        db_index=True,
    )
    preferred_time = models.TimeField(
        _("ساعت ترجیحی"),
        null=True,
        blank=True,
    )

    # ─── یادداشت ───
    note = models.CharField(
        _("یادداشت"),
        max_length=200,
        blank=True,
    )

    # ─── وضعیت ───
    status = models.CharField(
        _("وضعیت"),
        max_length=15,
        choices=WaitingStatus.choices,
        default=WaitingStatus.WAITING,
        db_index=True,
    )

    # ─── Manager ───
    objects = WaitingListManager()

    class Meta:
        verbose_name = _("لیست انتظار")
        verbose_name_plural = _("لیست‌های انتظار")
        ordering = ["date", "preferred_time", "created_at"]
        indexes = [
            models.Index(fields=["business", "status", "date"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.customer.display_name} → {self.business.name} | {self.date}"
        )

    # ═══════════════════════════════════════════════════════════
    #  Properties
    # ═══════════════════════════════════════════════════════════

    @property
    def is_waiting(self) -> bool:
        return self.status == WaitingStatus.WAITING

    @property
    def is_active(self) -> bool:
        """آیا هنوز قابل پردازشه؟"""
        return self.status in [
            WaitingStatus.WAITING,
            WaitingStatus.NOTIFIED,
        ]

    # ═══════════════════════════════════════════════════════════
    #  Methods
    # ═══════════════════════════════════════════════════════════

    def mark_notified(self) -> None:
        """علامت‌گذاری به‌عنوان اطلاع‌داده‌شده."""
        self.status = WaitingStatus.NOTIFIED
        self.save(update_fields=["status", "updated_at"])

    def mark_converted(self) -> None:
        """تبدیل به نوبت."""
        self.status = WaitingStatus.CONVERTED
        self.save(update_fields=["status", "updated_at"])

    def cancel(self) -> None:
        """لغو."""
        self.status = WaitingStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])


# ═══════════════════════════════════════════════════════════════
#  ۳. BlockedCustomer
# ═══════════════════════════════════════════════════════════════


class BlockedCustomer(TimeStampedModel):
    """
    مشتری بلاک‌شده.

    ─── چرا؟ ───
    بعضی مشتری‌ها ممکنه:
    - کنسل مکرر کنن
    - رفتار نامناسب داشته باشن
    - نیان (no-show)

    کسب‌وکار می‌تونه شماره‌شون رو بلاک کنه.

    ─── نکته: ───
    بلاک بر اساس شماره‌ست، نه user.
    اینطوری حتی اگه کاربر با شماره‌ی دیگه‌ای بیاد هم قابل شناساییه.
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="blocked_customers",
        verbose_name=_("کسب‌وکار"),
    )
    phone = models.CharField(
        _("شماره موبایل"),
        max_length=11,
        db_index=True,
    )
    name = models.CharField(
        _("نام"),
        max_length=100,
        blank=True,
    )
    reason = models.CharField(
        _("دلیل"),
        max_length=200,
        blank=True,
    )

    # ─── Manager ───
    objects = BlockedCustomerManager()

    class Meta:
        verbose_name = _("مشتری بلاک‌شده")
        verbose_name_plural = _("مشتری‌های بلاک‌شده")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "phone"],
                name="unique_blocked_business_phone",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.business.name} — {self.phone}"

    def save(self, *args, **kwargs) -> None:
        """نرمال‌سازی شماره + تلاش برای پر کردن name."""
        # ─── نرمال‌سازی ───
        normalized = normalize_phone(self.phone)
        if normalized:
            self.phone = normalized

        # ─── پر کردن name از مشتری ───
        if not self.name and self.phone:
            from apps.accounts.models import User

            customer = User.objects.filter(
                phone=self.phone,
                role=Role.CUSTOMER,
            ).first()
            if customer:
                self.name = customer.display_name

        super().save(*args, **kwargs)