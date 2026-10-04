"""
تست Integration جریان سالن.
"""

from datetime import time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.business.models import Service, StaffSchedule, StaffService, Station
from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment


@pytest.mark.django_db
class TestSalonFlow:
    """جریان کامل سالن."""

    def test_salon_reservation_with_staff_schedule(
        self,
        salon,
        salon_station,
        customer,
        next_saturday,
    ):
        """رزرو در سالن با شیفت کارمند."""
        from tests.factories import ServiceFactory, StaffFactory, StaffService

        # ۱. کارمند + شیفت
        staff = StaffFactory(business=salon, name="نرگس")
        for wd in range(0, 6):
            StaffSchedule.objects.create(
                staff=staff,
                station=salon_station,
                weekday=wd,
                start_time=time(9, 0),
                end_time=time(14, 0),
            )

        # ۲. خدمت
        service = ServiceFactory(
            business=salon,
            station=salon_station,
            name="کوتاهی مو",
            duration=30,
        )
        StaffService.objects.create(
            staff=staff,
            service=service,
            station=salon_station,
        )

        # ۳. رزرو
        from apps.booking.services import BookingService

        start = timezone.make_aware(
            timezone.datetime.combine(next_saturday, time(10, 0)),
            timezone.get_current_timezone(),
        )
        appt = BookingService(salon).create_appointment(
            customer=customer,
            service=service,
            start_at=start,
            staff=staff,
        )

        assert appt.pk is not None
        assert appt.staff == staff
        assert appt.station == salon_station