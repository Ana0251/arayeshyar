"""
سرویس ایجاد/لغو نوبت.
"""

import logging
from datetime import date, datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.business.models import Business, Service, Staff, Station

from ..constants import AppointmentStatus, MAX_BOOKING_DAYS_AHEAD
from ..models import Appointment, BlockedCustomer
from .availability import AvailabilityService

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Exceptions
# ═══════════════════════════════════════════════════════════════


class BookingError(ValidationError):
    """خطای عمومی booking."""


class BusinessNotActiveError(BookingError):
    """کسب‌وکار فعال نیست."""


class CustomerBlockedError(BookingError):
    """مشتری بلاک شده."""


class SlotNotAvailableError(BookingError):
    """اسلات آزاد نیست."""


class DuplicateBookingError(BookingError):
    """مشتری سر این ساعت نوبت دیگه داره."""


class TooFarAheadError(BookingError):
    """تاریخ نوبت خیلی دور است."""


# ═══════════════════════════════════════════════════════════════
#  BookingService
# ═══════════════════════════════════════════════════════════════


class BookingService:
    """
    سرویس ایجاد/لغو نوبت.

    ─── قواعد: ───
    1. کسب‌وکار باید فعال باشه
    2. مشتری نباید بلاک شده باشه
    3. اسلات باید آزاد باشه
    4. مشتری نباید سر همون ساعت جای دیگه نوبت داشته باشه
    5. نوبت نباید بیشتر از MAX_BOOKING_DAYS_AHEAD روز آینده باشه
    6. اگه auto_confirm → مستقیم confirmed

    ─── Race Condition: ───
    از `select_for_update` روی Business استفاده می‌کنیم.
    """

    def __init__(self, business: Business) -> None:
        self.business = business

    # ═══════════════════════════════════════════════════════════
    #  Create
    # ═══════════════════════════════════════════════════════════

    @transaction.atomic
    def create_appointment(
        self,
        *,
        customer: User,
        service: Service,
        start_at: datetime,
        staff: Staff | None = None,
        customer_note: str = "",
        created_by: User | None = None,
        force: bool = False,
    ) -> Appointment:
        """
        ایجاد نوبت جدید.

        Args:
            customer: مشتری
            service: خدمت
            start_at: زمان شروع
            staff: کارمند (اگه مشخص باشه)
            customer_note: یادداشت مشتری
            created_by: چه کسی ساخت (برای ثبت دستی)
            force: اگه True، تداخل رو نادیده بگیر (فقط برای ثبت دستی)

        Returns:
            Appointment

        Raises:
            BusinessNotActiveError, CustomerBlockedError,
            SlotNotAvailableError, DuplicateBookingError, TooFarAheadError
        """
        # ═══════════════════════════════════════════════════════════
        #  قفل روی Business (race condition guard)
        # ═══════════════════════════════════════════════════════════
        if not force:
            Business.objects.select_for_update().get(pk=self.business.pk)
            self.business.refresh_from_db()

        # ─── ۱. کسب‌وکار فعاله؟ ───
        if not self.business.is_active and not force:
            raise BusinessNotActiveError("این کسب‌وکار هنوز تأیید نشده.")

        # ─── ۲. مشتری بلاک نیست؟ ───
        if BlockedCustomer.objects.is_blocked(self.business, customer.phone):
            raise CustomerBlockedError("امکان رزرو برای شما وجود نداره.")

        # ─── ۳. تعیین staff ───
        if not staff:
            service_staff = list(
                service.staff_members.filter(is_active=True)
            )
            if len(service_staff) == 1:
                staff = service_staff[0]

        # ─── ۴. محاسبه‌ی زمان ───
        duration = service.duration
        end_at = start_at + timedelta(minutes=duration)

        # ─── ۵. چک بازه‌ی مجاز (حداکثر ۷ روز آینده) ───
        if not force:
            self._check_booking_range(start_at)

        # ─── ۶. چک اسلات (دوباره، بعد از قفل) ───
        if not force:
            availability = AvailabilityService(
                self.business,
                start_at.date(),
                station=service.station,
                staff=staff,
            )
            if not availability.is_slot_available(start_at, duration):
                raise SlotNotAvailableError(
                    "این ساعت در دسترس نیست. لطفاً یه ساعت دیگه انتخاب کن."
                )

        # ─── ۷. چک نوبت تکراری مشتری ───
        if not force:
            self._check_customer_double_booking(customer, start_at)

        # ─── ۸. وضعیت اولیه ───
        initial_status = (
            AppointmentStatus.CONFIRMED
            if self.business.auto_confirm or force
            else AppointmentStatus.PENDING
        )

        # ═══════════════════════════════════════════════════════════
        #  ساخت نوبت (با try/except برای UniqueConstraint)
        # ═══════════════════════════════════════════════════════════
        try:
            appointment = Appointment.objects.create(
                business=self.business,
                customer=customer,
                service=service,
                station=service.station,
                staff=staff,
                service_name_snapshot=service.name,
                service_price_snapshot=service.price,
                service_duration_snapshot=service.duration,
                start_at=start_at,
                end_at=end_at,
                status=initial_status,
                customer_note=customer_note,
                created_by=created_by,
                confirmed_at=(
                    timezone.now()
                    if initial_status == AppointmentStatus.CONFIRMED
                    else None
                ),
            )

        except IntegrityError as exc:
            logger.warning(
                f"Double booking prevented by DB constraint: "
                f"staff={staff}, station={service.station}, start_at={start_at}"
            )
            raise SlotNotAvailableError(
                "این ساعت همین الان رزرو شد. لطفاً یه ساعت دیگه انتخاب کن."
            ) from exc

        logger.info(
            f"Appointment #{appointment.pk} created: "
            f"{customer.phone} → {self.business.name} @ {start_at}"
        )

        return appointment

    # ═══════════════════════════════════════════════════════════
    #  Cancel / Confirm
    # ═══════════════════════════════════════════════════════════

    @transaction.atomic
    def cancel_appointment(
        self,
        appointment: Appointment,
        *,
        by_user: User | None = None,
        reason: str = "",
    ) -> Appointment:
        """لغو نوبت."""
        appointment.cancel(reason=reason, by_user=by_user)
        logger.info(f"Appointment #{appointment.pk} cancelled by {by_user}")
        return appointment

    @transaction.atomic
    def confirm_appointment(
        self,
        appointment: Appointment,
        *,
        by_user: User | None = None,
    ) -> Appointment:
        """تأیید نوبت."""
        appointment.confirm(by_user=by_user)
        return appointment

    # ═══════════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════════

    def _check_booking_range(self, start_at: datetime) -> None:
        """
        چک: نوبت توی بازه‌ی مجاز هست؟

        ─── قاعده: ───
        حداکثر تا MAX_BOOKING_DAYS_AHEAD روز آینده.
        """
        now_local = timezone.localtime(timezone.now())
        booking_date = timezone.localtime(start_at).date()
        max_date = now_local.date() + timedelta(days=MAX_BOOKING_DAYS_AHEAD)

        if booking_date > max_date:
            raise TooFarAheadError(
                f"حداکثر می‌تونی تا {MAX_BOOKING_DAYS_AHEAD} روز آینده نوبت بگیری."
            )

        # ─── چک نوبت توی گذشته ───
        if start_at < timezone.now():
            raise BookingError("نمی‌تونی برای زمان گذشته نوبت بگیری.")

    def _check_customer_double_booking(
        self,
        customer: User,
        start_at: datetime,
    ) -> None:
        """
        چک: مشتری سر این ساعت جای دیگه نوبت نداره؟
        """
        buffer = timedelta(minutes=1)
        check_start = start_at - buffer
        check_end = start_at + buffer

        conflict = (
            Appointment.objects.filter(customer=customer)
            .exclude(
                status__in=[
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.COMPLETED,
                ]
            )
            .filter(
                start_at__lt=check_end,
                end_at__gt=check_start,
            )
            .exists()
        )

        if conflict:
            raise DuplicateBookingError(
                "شما سر این ساعت یه نوبت دیگه دارید."
            )

    def get_available_slots(
        self,
        target_date: date,
        duration: int,
        station: Station | None = None,
        staff: Staff | None = None,
    ) -> list[time]:
        """اسلات‌های آزاد."""
        availability = AvailabilityService(
            self.business,
            target_date,
            station=station,
            staff=staff,
        )
        return availability.get_available_slots(duration)