"""
تست‌های Race Condition (Double Booking).
"""

from datetime import time, timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment


def _make_dt(target_date, hour, minute=0):
    from datetime import datetime

    naive = datetime.combine(target_date, time(hour, minute))
    return timezone.make_aware(naive, timezone.get_current_timezone())


@pytest.mark.django_db
class TestRaceCondition:
    """جلوگیری از double booking."""

    def test_db_constraint_prevents_double_booking(
        self,
        business,
        service_with_working_hours,
        customer,
        owner_staff,
        station,
        next_saturday,
    ):
        """DB باید جلوی نوبت تکراری رو بگیره."""
        start = _make_dt(next_saturday, 10, 0)

        # نوبت اول
        Appointment.objects.create(
            business=business,
            customer=customer,
            service=service_with_working_hours,
            staff=owner_staff,
            station=station,
            service_name_snapshot="test",
            service_price_snapshot=100_000,
            service_duration_snapshot=30,
            start_at=start,
            end_at=start + timedelta(minutes=30),
            status=AppointmentStatus.CONFIRMED,
        )

        # نوبت دوم با همون staff + start_at
        with pytest.raises(IntegrityError):
            Appointment.objects.create(
                business=business,
                customer=customer,
                service=service_with_working_hours,
                staff=owner_staff,
                station=station,
                service_name_snapshot="test",
                service_price_snapshot=100_000,
                service_duration_snapshot=30,
                start_at=start,
                end_at=start + timedelta(minutes=30),
                status=AppointmentStatus.CONFIRMED,
            )