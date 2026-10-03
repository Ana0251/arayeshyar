"""
سرویس مدیریت لیست انتظار.
"""

import logging
from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.business.models import Business, Service

from ..constants import WaitingStatus
from ..models import WaitingList

logger = logging.getLogger(__name__)


class WaitingListService:
    """سرویس مدیریت لیست انتظار."""

    def __init__(self, business: Business) -> None:
        self.business = business

    # ═══════════════════════════════════════════════════════════
    #  Add
    # ═══════════════════════════════════════════════════════════

    @transaction.atomic
    def add_to_waiting_list(
        self,
        *,
        customer: User,
        service: Service,
        target_date: date,
        preferred_time=None,
        note: str = "",
    ) -> WaitingList:
        """
        اضافه کردن مشتری به لیست انتظار.

        ─── چک تکراری: ───
        اگه قبلاً برای این تاریخ توی لیست باشه، همون برمی‌گرده.
        """
        # ─── چک تکراری ───
        existing = WaitingList.objects.filter(
            business=self.business,
            customer=customer,
            date=target_date,
            status=WaitingStatus.WAITING,
        ).first()

        if existing:
            return existing

        # ─── ساخت ───
        item = WaitingList.objects.create(
            business=self.business,
            customer=customer,
            service=service,
            service_name_snapshot=service.name,
            date=target_date,
            preferred_time=preferred_time,
            note=note,
            status=WaitingStatus.WAITING,
        )

        logger.info(
            f"WaitingList #{item.pk} created: "
            f"{customer.phone} → {self.business.name} @ {target_date}"
        )

        return item

    # ═══════════════════════════════════════════════════════════
    #  Actions
    # ═══════════════════════════════════════════════════════════

    @transaction.atomic
    def mark_notified(self, item: WaitingList) -> WaitingList:
        """علامت‌گذاری به‌عنوان اطلاع‌داده‌شده."""
        item.mark_notified()
        return item

    @transaction.atomic
    def mark_converted(self, item: WaitingList) -> WaitingList:
        """علامت‌گذاری به‌عنوان تبدیل‌شده."""
        item.mark_converted()
        return item

    @transaction.atomic
    def cancel(self, item: WaitingList) -> WaitingList:
        """لغو."""
        item.cancel()
        return item

    # ═══════════════════════════════════════════════════════════
    #  Cleanup
    # ═══════════════════════════════════════════════════════════

    def expire_past_items(self) -> int:
        """
        منقضی کردن آیتم‌های گذشته.

        آیتم‌هایی که تاریخشون گذشته و هنوز WAITING هستن.
        """
        today = timezone.localdate()
        count = WaitingList.objects.filter(
            business=self.business,
            date__lt=today,
            status=WaitingStatus.WAITING,
        ).update(status=WaitingStatus.EXPIRED)

        if count:
            logger.info(f"Expired {count} waiting list items")

        return count