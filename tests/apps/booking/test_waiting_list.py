"""
تست‌های WaitingListService.
"""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.booking.constants import WaitingStatus
from apps.booking.models import WaitingList
from apps.booking.services import WaitingListService


@pytest.mark.django_db
class TestWaitingListService:
    """تست‌های لیست انتظار."""

    def test_add_to_waiting_list(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        service = service_with_working_hours
        wl = WaitingListService(business)

        item = wl.add_to_waiting_list(
            customer=customer,
            service=service,
            target_date=next_saturday,
            preferred_time=time(10, 0),
            note="فقط صبح",
        )

        assert item.pk is not None
        assert item.status == WaitingStatus.WAITING
        assert item.customer == customer
        assert item.business == business

    def test_duplicate_returns_existing(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        service = service_with_working_hours
        wl = WaitingListService(business)

        item1 = wl.add_to_waiting_list(
            customer=customer,
            service=service,
            target_date=next_saturday,
        )
        item2 = wl.add_to_waiting_list(
            customer=customer,
            service=service,
            target_date=next_saturday,
        )

        # باید همون item1 برنگرده
        assert item1.pk == item2.pk

    def test_mark_notified(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        wl = WaitingListService(business)
        item = wl.add_to_waiting_list(
            customer=customer,
            service=service_with_working_hours,
            target_date=next_saturday,
        )

        wl.mark_notified(item)
        item.refresh_from_db()
        assert item.status == WaitingStatus.NOTIFIED

    def test_cancel(
        self, business, service_with_working_hours, customer, next_saturday
    ):
        wl = WaitingListService(business)
        item = wl.add_to_waiting_list(
            customer=customer,
            service=service_with_working_hours,
            target_date=next_saturday,
        )

        wl.cancel(item)
        item.refresh_from_db()
        assert item.status == WaitingStatus.CANCELLED

    def test_expire_past_items(
        self, business, service_with_working_hours, customer
    ):
        past_date = timezone.localdate() - timedelta(days=1)

        # ساخت مستقیم با تاریخ گذشته
        WaitingList.objects.create(
            business=business,
            customer=customer,
            service=service_with_working_hours,
            service_name_snapshot=service_with_working_hours.name,
            date=past_date,
            status=WaitingStatus.WAITING,
        )

        wl = WaitingListService(business)
        count = wl.expire_past_items()

        assert count == 1
        assert WaitingList.objects.filter(
            status=WaitingStatus.EXPIRED
        ).count() == 1