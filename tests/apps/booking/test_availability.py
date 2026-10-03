"""
تست‌های AvailabilityService.

─── نکته: ───
این تست‌ها قلب پروژه هستن — اگه اسلات‌ها غلط باشن، همه‌چیز غلط میشه.
"""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.booking.models import Appointment
from apps.booking.constants import AppointmentStatus
from apps.booking.services import AvailabilityService
from apps.business.models import Break, WorkingHours


# ═══════════════════════════════════════════════════════════════
#  Get Business Hours
# ═══════════════════════════════════════════════════════════════


class TestBusinessHours:
    """تست‌های ساعت کاری."""

    def test_no_hours_returns_empty(self, business, service, next_saturday):
        """کسب‌وکار بدون برنامه هفتگی → اسلات خالی."""
        availability = AvailabilityService(business, next_saturday)
        slots = availability.get_available_slots(duration=30)

        assert slots == []

    def test_business_hours_used(self, business_with_hours, service, next_saturday):
        """ساعت کاری درست اعمال میشه."""
        availability = AvailabilityService(business_with_hours, next_saturday)
        slots = availability.get_available_slots(duration=30)

        # ─── از ۹ تا ۲۱ با گام ۳۰ دقیقه = ۲۴ اسلات ───
        assert len(slots) == 24
        assert slots[0].hour == 9
        assert slots[0].minute == 0
        assert slots[-1].hour == 20
        assert slots[-1].minute == 30


# ═══════════════════════════════════════════════════════════════
#  Booked Slots
# ═══════════════════════════════════════════════════════════════


class TestBookedSlots:
    """تست‌های اسلات‌های رزرو‌شده."""

    def test_booked_slot_excluded(
        self,
        business_with_hours,
        service,
        customer,
        owner_staff,
        station,
        next_saturday,
    ):
        """اسلات رزرو‌شده توی لیست نمیاد."""
        # ─── یه نوبت ساعت ۱۰:۰۰ ───
        start_at = timezone.make_aware(
            timezone.datetime.combine(next_saturday, time(10, 0)),
            timezone.get_current_timezone(),
        )

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

        availability = AvailabilityService(
            business_with_hours,
            next_saturday,
        )
        slots = availability.get_available_slots(duration=30)

        # ─── ساعت ۱۰:۰۰ نباید باشه ───
        slot_times = [(s.hour, s.minute) for s in slots]
        assert (10, 0) not in slot_times


# ═══════════════════════════════════════════════════════════════
#  Break Slots
# ═══════════════════════════════════════════════════════════════


class TestBreakSlots:
    """تست‌های وقفه استراحت."""

    def test_break_excluded(
        self,
        business_with_hours,
        service,
        next_saturday,
    ):
        """وقفه استراحت توی لیست نمیاد."""
        # ─── وقفه از ۱۳:۰۰ تا ۱۴:۰۰ ───
        Break.objects.create(
            business=business_with_hours,
            station=None,
            start_time=time(13, 0),
            end_time=time(14, 0),
            label="ناهار",
            is_active=True,
        )

        availability = AvailabilityService(
            business_with_hours,
            next_saturday,
        )
        slots = availability.get_available_slots(duration=30)

        slot_times = [(s.hour, s.minute) for s in slots]

        # ─── ساعت ۱۳:۰۰ و ۱۳:۳۰ نباید باشن ───
        assert (13, 0) not in slot_times
        assert (13, 30) not in slot_times

        # ─── ولی ۱۲:۳۰ و ۱۴:۰۰ باید باشن ───
        assert (12, 30) in slot_times
        assert (14, 0) in slot_times