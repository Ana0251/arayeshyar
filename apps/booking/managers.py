"""
Manager های سفارشی برای اپ booking.
"""

from datetime import date, datetime

from django.db import models
from django.utils import timezone


class AppointmentQuerySet(models.QuerySet):
    """QuerySet سفارشی برای Appointment."""

    def active(self) -> "AppointmentQuerySet":
        """نوبت‌های فعال (نه لغو شده)."""
        return self.exclude(status="cancelled")

    def pending(self) -> "AppointmentQuerySet":
        """نوبت‌های در انتظار تأیید."""
        return self.filter(status="pending")

    def confirmed(self) -> "AppointmentQuerySet":
        """نوبت‌های تأییدشده."""
        return self.filter(status="confirmed")

    def for_date(self, target_date: date) -> "AppointmentQuerySet":
        """نوبت‌های یه تاریخ مشخص."""
        return self.filter(start_at__date=target_date)

    def for_business(self, business) -> "AppointmentQuerySet":
        """نوبت‌های یه کسب‌وکار."""
        return self.filter(business=business)

    def for_customer(self, customer) -> "AppointmentQuerySet":
        """نوبت‌های یه مشتری."""
        return self.filter(customer=customer)

    def upcoming(self) -> "AppointmentQuerySet":
        """نوبت‌های آینده."""
        return self.filter(start_at__gte=timezone.now()).exclude(
            status="cancelled"
        )

    def past(self) -> "AppointmentQuerySet":
        """نوبت‌های گذشته."""
        return self.filter(start_at__lt=timezone.now())

    def overlapping(
        self,
        start: datetime,
        end: datetime,
    ) -> "AppointmentQuerySet":
        """
        نوبت‌هایی که با بازه‌ی [start, end] تداخل دارن.

        ─── فرمول تداخل: ───
        appointment.start < end AND appointment.end > start
        """
        return self.exclude(status="cancelled").filter(
            start_at__lt=end,
            end_at__gt=start,
        )

    def with_relations(self) -> "AppointmentQuerySet":
        """با relation های اصلی join شده."""
        return self.select_related(
            "business",
            "customer",
            "service",
            "station",
        )


class AppointmentManager(models.Manager):
    """
    Manager پیش‌فرض Appointment.

    ─── نکته: ───
    همه‌ی متدهای QuerySet اینجا هم تعریف میشن تا بتونیم
    مستقیم از `Appointment.objects.for_business(...)` استفاده کنیم.
    """

    def get_queryset(self) -> AppointmentQuerySet:
        return AppointmentQuerySet(self.model, using=self._db)

    # ═══════════════════════════════════════════════════════════
    #  Delegates به QuerySet
    # ═══════════════════════════════════════════════════════════

    def active(self) -> AppointmentQuerySet:
        return self.get_queryset().active()

    def pending(self) -> AppointmentQuerySet:
        return self.get_queryset().pending()

    def confirmed(self) -> AppointmentQuerySet:
        return self.get_queryset().confirmed()

    def for_date(self, target_date: date) -> AppointmentQuerySet:
        return self.get_queryset().for_date(target_date)

    def for_business(self, business) -> AppointmentQuerySet:
        return self.get_queryset().for_business(business)

    def for_customer(self, customer) -> AppointmentQuerySet:
        return self.get_queryset().for_customer(customer)

    def upcoming(self) -> AppointmentQuerySet:
        return self.get_queryset().upcoming()

    def past(self) -> AppointmentQuerySet:
        return self.get_queryset().past()

    def overlapping(
        self,
        start: datetime,
        end: datetime,
    ) -> AppointmentQuerySet:
        return self.get_queryset().overlapping(start, end)

    def with_relations(self) -> AppointmentQuerySet:
        return self.get_queryset().with_relations()


class WaitingListQuerySet(models.QuerySet):
    """QuerySet سفارشی برای WaitingList."""

    def waiting(self) -> "WaitingListQuerySet":
        """آیتم‌های در انتظار."""
        return self.filter(status="waiting")

    def active(self) -> "WaitingListQuerySet":
        """آیتم‌های فعال (نه لغو/منقضی)."""
        return self.exclude(status__in=["cancelled", "expired", "converted"])

    def for_date(self, target_date: date) -> "WaitingListQuerySet":
        """آیتم‌های یه تاریخ."""
        return self.filter(date=target_date)

    def for_business(self, business) -> "WaitingListQuerySet":
        """آیتم‌های یه کسب‌وکار."""
        return self.filter(business=business)


class WaitingListManager(models.Manager):
    """Manager پیش‌فرض WaitingList."""

    def get_queryset(self) -> WaitingListQuerySet:
        return WaitingListQuerySet(self.model, using=self._db)

    def waiting(self) -> WaitingListQuerySet:
        return self.get_queryset().waiting()

    def active(self) -> WaitingListQuerySet:
        return self.get_queryset().active()

    def for_date(self, target_date: date) -> WaitingListQuerySet:
        return self.get_queryset().for_date(target_date)

    def for_business(self, business) -> WaitingListQuerySet:
        return self.get_queryset().for_business(business)


class BlockedCustomerQuerySet(models.QuerySet):
    """QuerySet سفارشی برای BlockedCustomer."""

    def for_business(self, business) -> "BlockedCustomerQuerySet":
        return self.filter(business=business)

    def with_phone(self, phone: str) -> "BlockedCustomerQuerySet":
        return self.filter(phone=phone)


class BlockedCustomerManager(models.Manager):
    """Manager پیش‌فرض BlockedCustomer."""

    def get_queryset(self) -> BlockedCustomerQuerySet:
        return BlockedCustomerQuerySet(self.model, using=self._db)

    def for_business(self, business) -> BlockedCustomerQuerySet:
        return self.get_queryset().for_business(business)

    def with_phone(self, phone: str) -> BlockedCustomerQuerySet:
        return self.get_queryset().with_phone(phone)

    def is_blocked(self, business, phone: str) -> bool:
        """آیا این شماره توسط این کسب‌وکار بلاک شده؟"""
        from apps.core.utils.phone import normalize_phone

        normalized = normalize_phone(phone)
        if not normalized:
            return False

        return self.filter(business=business, phone=normalized).exists()