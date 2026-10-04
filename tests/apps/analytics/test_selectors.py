"""
تست‌های selectors اپ analytics.
"""

from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone

from apps.analytics.selectors import (
    get_golden_hours,
    get_golden_weekdays,
    get_overall_stats,
    get_service_stats,
)
from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment


@pytest.mark.django_db
class TestAnalyticsSelectors:
    """تست selectors آماری."""

    def test_overall_stats_empty(self, business):
        stats = get_overall_stats(business, days=30)
        assert stats["total_appointments"] == 0
        assert stats["total_revenue"] == 0

    def test_overall_stats_with_appointments(
        self, business, service, customer, owner_staff
    ):
        # ─── نوبت توی گذشته ───
        start = timezone.now() - timedelta(days=1)
        Appointment.objects.create(
            business=business,
            customer=customer,
            service=service,
            staff=owner_staff,
            station=service.station,
            service_name_snapshot=service.name,
            service_price_snapshot=150_000,
            service_duration_snapshot=30,
            start_at=start,
            end_at=start + timedelta(minutes=30),
            status=AppointmentStatus.COMPLETED,
        )

        stats = get_overall_stats(business, days=30)
        assert stats["total_appointments"] == 1
        assert stats["total_revenue"] == 150_000
        assert stats["completed_count"] == 1

    def test_golden_hours(self, business, service, customer, owner_staff):
        """
        ساعت طلایی = ساعتی که بیشترین نوبت رو داره.

        ─── نکته: ───
        ساعت رو با timezone Tehran می‌سازیم تا با localtime() توی selector هماهنگ باشه.
        """
        for i in range(3):
            target_date = timezone.localdate() - timedelta(days=i + 1)
            naive = datetime.combine(target_date, time(10, 0))
            start = timezone.make_aware(naive, timezone.get_current_timezone())

            Appointment.objects.create(
                business=business,
                customer=customer,
                service=service,
                staff=owner_staff,
                station=service.station,
                service_name_snapshot=service.name,
                service_price_snapshot=100_000,
                service_duration_snapshot=30,
                start_at=start,
                end_at=start + timedelta(minutes=30),
                status=AppointmentStatus.COMPLETED,
            )

        hours = get_golden_hours(business, days=30)
        assert len(hours) > 0
        assert any(h["hour"] == 10 for h in hours)

    def test_service_stats(self, business, service, customer, owner_staff):
        for i in range(5):
            start = timezone.now() - timedelta(days=i + 1)
            Appointment.objects.create(
                business=business,
                customer=customer,
                service=service,
                staff=owner_staff,
                station=service.station,
                service_name_snapshot=service.name,
                service_price_snapshot=100_000,
                service_duration_snapshot=30,
                start_at=start,
                end_at=start + timedelta(minutes=30),
                status=AppointmentStatus.COMPLETED,
            )

        stats = get_service_stats(business, days=30)
        assert len(stats) == 1
        assert stats[0]["service_name"] == service.name
        assert stats[0]["count"] == 5