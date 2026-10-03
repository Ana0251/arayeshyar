"""
تست‌های BookingService (ایجاد نوبت).

─── نکته: ───
این تست‌ها قوانین اصلی booking رو چک می‌کنن.
"""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment
from apps.booking.services import (
    BookingService,
    BusinessNotActiveError,
    CustomerBlockedError,
    SlotNotAvailableError,
)
from apps.booking.models import BlockedCustomer


# ═══════════════════════════════════════════════════════════════
#  Helper
# ═══════════════════════════════════════════════════════════════


def _make_start_at(target_date, hour=10, minute=0):
    """ساخت datetime aware (Tehran) از تاریخ و ساعت."""
    naive = timezone.datetime.combine(
        target_date,
        time(hour, minute),
    )
    return timezone.make_aware(naive, timezone.get_current_timezone())


# ═══════════════════════════════════════════════════════════════
#  Create Appointment
# ═══════════════════════════════════════════════════════════════


class TestCreateAppointment:
    """تست‌های create_appointment."""

    def test_create_basic(
        self,
        business_with_hours,
        service,
        customer,
        owner_staff,
        next_saturday,
    ):
        """ایجاد نوبت ساده."""
        start_at = _make_start_at(next_saturday, 10, 0)

        bs = BookingService(business_with_hours)
        appt = bs.create_appointment(
            customer=customer,
            service=service,
            start_at=start_at,
            staff=owner_staff,
        )

        assert appt.pk is not None
        assert appt.customer == customer
        assert appt.service == service
        assert appt.staff == owner_staff
        assert appt.start_at == start_at
        assert appt.end_at == start_at + timedelta(minutes=30)
        # ─── auto_confirm=True ───
        assert appt.status == AppointmentStatus.CONFIRMED

    def test_create_inactive_business_fails(
        self,
        business_with_hours,
        service,
        customer,
        owner_staff,
        next_saturday,
    ):
        """کسب‌وکار غیرفعال → خطا."""
        business_with_hours.is_active = False
        business_with_hours.save()

        start_at = _make_start_at(next_saturday, 10, 0)

        bs = BookingService(business_with_hours)
        with pytest.raises(BusinessNotActiveError):
            bs.create_appointment(
                customer=customer,
                service=service,
                start_at=start_at,
                staff=owner_staff,
            )

    def test_create_blocked_customer_fails(
        self,
        business_with_hours,
        service,
        customer,
        owner_staff,
        next_saturday,
    ):
        """مشتری بلاک‌شده → خطا."""
        BlockedCustomer.objects.create(
            business=business_with_hours,
            phone=customer.phone,
            reason="تست",
        )

        start_at = _make_start_at(next_saturday, 10, 0)

        bs = BookingService(business_with_hours)
        with pytest.raises(CustomerBlockedError):
            bs.create_appointment(
                customer=customer,
                service=service,
                start_at=start_at,
                staff=owner_staff,
            )

    def test_create_duplicate_slot_fails(
        self,
        business_with_hours,
        service,
        customer,
        owner_staff,
        next_saturday,
    ):
        """دو نوبت سر یه ساعت → خطا."""
        start_at = _make_start_at(next_saturday, 10, 0)

        bs = BookingService(business_with_hours)
        bs.create_appointment(
            customer=customer,
            service=service,
            start_at=start_at,
            staff=owner_staff,
        )

        # ─── نوبت دوم سر همون ساعت ───
        with pytest.raises(SlotNotAvailableError):
            bs.create_appointment(
                customer=customer,
                service=service,
                start_at=start_at,
                staff=owner_staff,
            )


# ═══════════════════════════════════════════════════════════════
#  Race Condition
# ═══════════════════════════════════════════════════════════════


class TestRaceCondition:
    """تست‌های جلوگیری از Double Booking."""

    def test_db_constraint_prevents_double_booking(
        self,
        business_with_hours,
        service,
        customer,
        owner_staff,
        station,
        next_saturday,
    ):
        """
        ─── نکته: ───
        این تست فرض می‌کنه UniqueConstraint روی (staff, start_at) هست.
        حتی اگه BookingService چک نکنه، DB باید جلوش رو بگیره.
        """
        from django.db import IntegrityError

        start_at = _make_start_at(next_saturday, 10, 0)

        # ─── نوبت اول ───
        Appointment.objects.create(
            business=business_with_hours,
            customer=customer,
            service=service,
            staff=owner_staff,
            station=station,
            service_name_snapshot=service.name,
            service_price_snapshot=service.price,
            service_duration_snapshot=service.duration,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=30),
            status=AppointmentStatus.CONFIRMED,
        )

        # ─── نوبت دوم (بدون چک BookingService) ───
        with pytest.raises(IntegrityError):
            Appointment.objects.create(
                business=business_with_hours,
                customer=customer,
                service=service,
                staff=owner_staff,
                station=station,
                service_name_snapshot=service.name,
                service_price_snapshot=service.price,
                service_duration_snapshot=service.duration,
                start_at=start_at,
                end_at=start_at + timedelta(minutes=30),
                status=AppointmentStatus.CONFIRMED,
            )