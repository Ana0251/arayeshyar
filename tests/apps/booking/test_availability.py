"""
تست‌های AvailabilityService.
"""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment
from apps.booking.services import AvailabilityService
from apps.business.models import Break, StaffSchedule, WorkingHours


def _make_dt(target_date, hour, minute=0):
    """datetime aware (Tehran)."""
    from datetime import datetime

    naive = datetime.combine(target_date, time(hour, minute))
    return timezone.make_aware(naive, timezone.get_current_timezone())


@pytest.mark.django_db
class TestAvailabilityPersonal:
    """تست‌های کسب‌وکار شخصی."""

    def test_slots_from_working_hours(
        self, business, service_with_working_hours, next_saturday
    ):
        availability = AvailabilityService(
            business, next_saturday, station=service_with_working_hours.station
        )
        slots = availability.get_available_slots(duration=30)
        # ۹ تا ۲۱ با گام ۳۰ دقیقه = ۲۴ اسلات
        assert len(slots) == 24
        assert slots[0].hour == 9
        assert slots[-1].hour == 20

    def test_booked_slot_excluded(
        self,
        business,
        service_with_working_hours,
        customer,
        owner_staff,
        station,
        next_saturday,
    ):
        start = _make_dt(next_saturday, 10, 0)

        Appointment.objects.create(
            business=business,
            customer=customer,
            service=service_with_working_hours,
            staff=owner_staff,
            station=station,
            service_name_snapshot=service_with_working_hours.name,
            service_price_snapshot=service_with_working_hours.price,
            service_duration_snapshot=30,
            start_at=start,
            end_at=start + timedelta(minutes=30),
            status=AppointmentStatus.CONFIRMED,
        )

        availability = AvailabilityService(
            business, next_saturday, station=station
        )
        slots = availability.get_available_slots(duration=30)

        slot_times = [(s.hour, s.minute) for s in slots]
        assert (10, 0) not in slot_times

    def test_past_date_returns_empty(
        self, business, service_with_working_hours
    ):
        past = timezone.localdate() - timedelta(days=1)
        availability = AvailabilityService(
            business, past, station=service_with_working_hours.station
        )
        assert availability.get_available_slots(30) == []

    def test_break_excluded(
        self, business, service_with_working_hours, next_saturday
    ):
        Break.objects.create(
            business=business,
            station=None,
            start_time=time(13, 0),
            end_time=time(14, 0),
            label="ناهار",
            is_active=True,
        )

        availability = AvailabilityService(
            business, next_saturday, station=service_with_working_hours.station
        )
        slots = availability.get_available_slots(duration=30)
        slot_times = [(s.hour, s.minute) for s in slots]

        assert (13, 0) not in slot_times
        assert (13, 30) not in slot_times
        assert (14, 0) in slot_times


@pytest.mark.django_db
class TestAvailabilitySalon:
    """تست‌های سالن."""

    def test_slots_from_staff_schedules(
        self, salon, salon_station, next_saturday
    ):
        staff1 = __import__("tests.factories", fromlist=["StaffFactory"]).StaffFactory(
            business=salon, name="کارمند ۱"
        )
        staff2 = __import__("tests.factories", fromlist=["StaffFactory"]).StaffFactory(
            business=salon, name="کارمند ۲"
        )

        # staff1: 9-14
        for wd in range(0, 6):
            StaffSchedule.objects.create(
                staff=staff1,
                station=salon_station,
                weekday=wd,
                start_time=time(9, 0),
                end_time=time(14, 0),
            )
            StaffSchedule.objects.create(
                staff=staff2,
                station=salon_station,
                weekday=wd,
                start_time=time(14, 0),
                end_time=time(21, 0),
            )

        iranian_wd = (next_saturday.weekday() + 2) % 7

        availability = AvailabilityService(
            salon, next_saturday, station=salon_station, staff=None
        )
        slots = availability.get_available_slots(duration=30)

        # union: 9-21
        assert len(slots) > 0
        slot_times = [(s.hour, s.minute) for s in slots]
        assert (9, 0) in slot_times
        assert (20, 30) in slot_times

    def test_staff_specific_filter(
        self, salon, salon_station, next_saturday
    ):
        from tests.factories import StaffFactory

        staff1 = StaffFactory(business=salon)
        staff2 = StaffFactory(business=salon)

        for wd in range(0, 6):
            StaffSchedule.objects.create(
                staff=staff1, station=salon_station, weekday=wd,
                start_time=time(9, 0), end_time=time(14, 0),
            )
            StaffSchedule.objects.create(
                staff=staff2, station=salon_station, weekday=wd,
                start_time=time(14, 0), end_time=time(21, 0),
            )

        # فقط staff1
        availability = AvailabilityService(
            salon, next_saturday, station=salon_station, staff=staff1
        )
        slots = availability.get_available_slots(duration=30)

        slot_times = [(s.hour, s.minute) for s in slots]
        assert (9, 0) in slot_times
        assert (13, 30) in slot_times
        # 14:00 به بعد نباید باشه
        assert (14, 0) not in slot_times
        assert (20, 30) not in slot_times