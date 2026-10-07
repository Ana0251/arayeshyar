"""
سرویس ایجاد/لغو نوبت.
"""

import logging
from datetime import date, datetime, time, timedelta

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.business.models import Business, Service, Staff, Station

from ..constants import (
    AppointmentStatus,
    BOOKING_RATE_WINDOW_SECONDS,
    MAX_ACTIVE_APPOINTMENTS_PER_CUSTOMER,
    MAX_BOOKINGS_PER_WINDOW,
    MAX_GLOBAL_ACTIVE_APPOINTMENTS_PER_CUSTOMER,
)
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


class TooManyActiveAppointmentsError(BookingError):
    """تعداد نوبت‌های فعال مشتری بیش از حد مجازه."""


class BookingRateLimitError(BookingError):
    """مشتری در بازه کوتاه تعداد زیادی رزرو موفق ثبت کرده."""


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
    5. اگه auto_confirm → مستقیم confirmed

    ─── Race Condition: ───
    برای جلوگیری از double booking، از `select_for_update` روی Business
    استفاده می‌کنیم. این باعث میشه رزروها برای یه کسب‌وکار سریال بشن.
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

        ─── Race Condition: ───
        1. قفل روی Business (select_for_update) → رزروهای یه business سریال میشن
        2. چک دوباره‌ی availability بعد از قفل
        3. اگه IntegrityError از UniqueConstraint اومد → SlotNotAvailableError

        ─── قیمت: ───
        اگه staff مشخص شده، از `StaffService.effective_price` استفاده کن.
        وگرنه از `Service.price`.

        ─── تعیین staff (اگه فرقی نمی‌کنه): ───
        - ۱ کارمند → خودکار
        - ۲+ کارمند → یه کارمند آزاد انتخاب کن
        - هیچ کارمند آزاد → خطا
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

        # ─── ۳. ضد سوءاستفاده / محدودیت رزرو مشتری ───
        # این کنترل عمداً داخل Service است تا با تغییر View/HTMX قابل دور زدن نباشد.
        if not force:
            self._enforce_customer_booking_limits(customer)

        # ─── ۴. تعیین staff ───
        if not staff:
            service_staff = self._get_service_staff(service)

            if len(service_staff) == 1:
                staff = service_staff[0]
            elif len(service_staff) > 1:
                # ─── یه کارمند آزاد انتخاب کن ───
                staff = self._pick_available_staff(
                    service_staff,
                    start_at,
                    service.duration,
                    service.station,
                )
                if not staff and not force:
                    raise SlotNotAvailableError(
                        "این ساعت هیچ کارمند آزادی نداره. لطفاً یه ساعت دیگه انتخاب کن."
                    )

        # ─── ۴. محاسبه‌ی زمان ───
        duration = service.duration
        end_at = start_at + timedelta(minutes=duration)

        # ─── ۵. چک اسلات (دوباره، بعد از قفل) ───
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

        # ─── ۶. چک نوبت تکراری مشتری ───
        if not force:
            self._check_customer_double_booking(customer, start_at)

        # ═══════════════════════════════════════════════════════════
        #  قیمت نهایی (از StaffService)
        # ═══════════════════════════════════════════════════════════
        final_price = self._get_final_price(service, staff)

        # ─── ۷. وضعیت اولیه ───
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
                station=service.station,  # ← خودکار از service
                staff=staff,
                service_name_snapshot=service.name,
                service_price_snapshot=final_price,  # ← از StaffService
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

        if not force:
            self._record_successful_booking(customer)

        logger.info(
            f"Appointment #{appointment.pk} created: "
            f"{customer.phone} → {self.business.name} @ {start_at}"
        )

        return appointment

    # ═══════════════════════════════════════════════════════════
    #  Cancel
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

    # ═══════════════════════════════════════════════════════════
    #  Confirm
    # ═══════════════════════════════════════════════════════════

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

    def _enforce_customer_booking_limits(self, customer: User) -> None:
        """
        محدودیت‌های ضد رزرو مزاحم.

        نوبت فعال یعنی PENDING/CONFIRMED که هنوز پایانش نگذشته باشد.
        استفاده از end_at به‌جای start_at باعث می‌شود نوبتی که در حال اجراست هم
        تا پایان واقعی‌اش فعال حساب شود.
        """
        now = timezone.now()
        active_statuses = [
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
        ]

        # استفاده از customer_id/business_id صریح است و به هیچ Manager سفارشی وابسته نیست.
        business_active_count = Appointment.objects.filter(
            customer_id=customer.pk,
            business_id=self.business.pk,
            status__in=active_statuses,
            end_at__gt=now,
        ).count()

        if business_active_count >= MAX_ACTIVE_APPOINTMENTS_PER_CUSTOMER:
            raise TooManyActiveAppointmentsError(
                f"شما در حال حاضر {MAX_ACTIVE_APPOINTMENTS_PER_CUSTOMER} نوبت فعال "
                "در این مجموعه دارید. برای رزرو جدید، یکی از نوبت‌های قبلی را "
                "لغو کنید یا بعد از انجام آن دوباره تلاش کنید."
            )

        global_active_count = Appointment.objects.filter(
            customer_id=customer.pk,
            status__in=active_statuses,
            end_at__gt=now,
        ).count()

        if global_active_count >= MAX_GLOBAL_ACTIVE_APPOINTMENTS_PER_CUSTOMER:
            raise TooManyActiveAppointmentsError(
                f"شما در حال حاضر {MAX_GLOBAL_ACTIVE_APPOINTMENTS_PER_CUSTOMER} نوبت فعال دارید. "
                "برای ثبت نوبت جدید، ابتدا یکی از نوبت‌های فعلی را لغو کنید یا منتظر انجام آن بمانید."
            )

        # نرخ رزرو موفق در بازه کوتاه. کلید فقط بر اساس customer است تا با رفتن
        # بین چند سالن نتوان محدودیت را دور زد.
        rate_key = f"booking:successful:{customer.pk}"
        recent_successes = int(cache.get(rate_key, 0) or 0)
        if recent_successes >= MAX_BOOKINGS_PER_WINDOW:
            raise BookingRateLimitError(
                "در مدت کوتاهی چند نوبت ثبت کرده‌اید. لطفاً حدود ۱۰ دقیقه بعد دوباره تلاش کنید."
            )

    def _record_successful_booking(self, customer: User) -> None:
        """فقط رزرو موفق را در Rate Limit ثبت می‌کند؛ خطاهای فرم جریمه نمی‌شوند."""
        rate_key = f"booking:successful:{customer.pk}"
        try:
            cache.incr(rate_key)
        except ValueError:
            cache.set(rate_key, 1, timeout=BOOKING_RATE_WINDOW_SECONDS)

    def _get_service_staff(self, service: Service) -> list[Staff]:
        """
        لیست کارمندهایی که این خدمت رو توی این اتاق انجام می‌دن.
        """
        from apps.business.models import StaffService

        staff_services = (
            StaffService.objects.filter(
                service=service,
                station=service.station,
                is_active=True,
                staff__is_active=True,
            )
            .select_related("staff")
            .order_by("staff__order", "staff__name")
        )

        return [ss.staff for ss in staff_services]

    def _pick_available_staff(
        self,
        staff_list: list[Staff],
        start_at: datetime,
        duration: int,
        station: Station,
    ) -> Staff | None:
        """
        انتخاب اولین کارمند آزاد برای یه ساعت مشخص.

        ─── چرا؟ ───
        وقتی مشتری «فرقی نمی‌کنه» رو می‌زنه، سیستم باید خودکار
        یه کارمند آزاد انتخاب کنه که توی شیفتش باشه.
        """
        for staff in staff_list:
            availability = AvailabilityService(
                self.business,
                start_at.date(),
                station=station,
                staff=staff,
            )
            if availability.is_slot_available(start_at, duration):
                return staff

        return None

    def _get_final_price(
        self,
        service: Service,
        staff: Staff | None,
    ) -> int:
        """
        قیمت نهایی خدمت.

        ─── منطق: ───
        - اگه staff مشخص شده و StaffService داره → effective_price
        - وگرنه → service.price
        """
        if not staff:
            return service.price

        from apps.business.models import StaffService

        ss = StaffService.objects.filter(
            staff=staff,
            service=service,
            station=service.station,
            is_active=True,
        ).first()

        if ss:
            return ss.effective_price

        return service.price

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