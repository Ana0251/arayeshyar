"""
تست‌های BookingService.
"""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment, BlockedCustomer
from apps.booking.services import (
    BookingService,
    BusinessNotActiveError,
    CustomerBlockedError,
    SlotNotAvailableError,
)


def _make_dt(target_date, hour, minute=0):
    from datetime import datetime

    naive = datetime.combine(target_date, time(hour, minute))
    return timezone.make_aware(naive, timezone.get_current_timezone())


@pytest.mark.django_db
class TestCreateAppointment:
    """تست‌های create_appointment."""

    def test_create_basic(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        start = _make_dt(next_saturday, 10, 0)
        bs = BookingService(business)
        appt = bs.create_appointment(
            customer=customer,
            service=service_with_working_hours,
            start_at=start,
        )
        assert appt.pk is not None
        assert appt.customer == customer
        assert appt.status == AppointmentStatus.CONFIRMED

    def test_inactive_business_fails(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        business.is_active = False
        business.save()

        with pytest.raises(BusinessNotActiveError):
            BookingService(business).create_appointment(
                customer=customer,
                service=service_with_working_hours,
                start_at=_make_dt(next_saturday, 10, 0),
            )

    def test_blocked_customer_fails(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        BlockedCustomer.objects.create(
            business=business,
            phone=customer.phone,
            reason="test",
        )

        with pytest.raises(CustomerBlockedError):
            BookingService(business).create_appointment(
                customer=customer,
                service=service_with_working_hours,
                start_at=_make_dt(next_saturday, 10, 0),
            )

    def test_duplicate_slot_fails(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        start = _make_dt(next_saturday, 10, 0)
        bs = BookingService(business)
        bs.create_appointment(
            customer=customer,
            service=service_with_working_hours,
            start_at=start,
        )

        with pytest.raises(SlotNotAvailableError):
            bs.create_appointment(
                customer=customer,
                service=service_with_working_hours,
                start_at=start,
            )
    @pytest.mark.skip(reason="TODO: نیاز به کسب‌وکار دوم")
    def test_customer_double_booking_fails(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        # دو نوبت با همون مشتری، در بازه‌های نزدیک
        bs = BookingService(business)
        bs.create_appointment(
            customer=customer,
            service=service_with_working_hours,
            start_at=_make_dt(next_saturday, 10, 0),
        )

        from apps.booking.services import DuplicateBookingError

        with pytest.raises(DuplicateBookingError):
            bs.create_appointment(
                customer=customer,
                service=service_with_working_hours,
                start_at=_make_dt(next_saturday, 10, 0),
                force=False,
            )

    def test_auto_confirm(self, business, service_with_working_hours, customer, next_saturday):
        business.auto_confirm = True
        business.save()

        appt = BookingService(business).create_appointment(
            customer=customer,
            service=service_with_working_hours,
            start_at=_make_dt(next_saturday, 10, 0),
        )
        assert appt.status == AppointmentStatus.CONFIRMED

    def test_pending_when_no_auto_confirm(
        self, salon, salon_station, next_saturday
    ):
        # سالن auto_confirm=False
        from tests.factories import ServiceFactory, StaffFactory, StaffService, StaffSchedule
        from apps.business.models import Service, Staff, StaffService

        staff = StaffFactory(business=salon)
        service = ServiceFactory(business=salon, station=salon_station, duration=30)

        StaffSchedule.objects.create(
            staff=staff, station=salon_station, weekday=0,
            start_time=time(9, 0), end_time=time(21, 0),
        )
        StaffService.objects.create(
            staff=staff, service=service, station=salon_station,
        )

        customer = __import__("tests.factories", fromlist=["CustomerUserFactory"]).CustomerUserFactory()
        customer.set_unusable_password()
        customer.save()

        appt = BookingService(salon).create_appointment(
            customer=customer,
            service=service,
            start_at=_make_dt(next_saturday, 10, 0),
        )
        assert appt.status == AppointmentStatus.PENDING