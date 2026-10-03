"""
Signal های اپ business.

هدف:
- ساخت BusinessOwnerProfile بعد از ساخت Business
- آپدیت role کاربر به business_owner
- تنظیم دوره‌ی تست
- ساخت Station پیش‌فرض برای کسب‌وکار شخصی
- ساخت Staff صاحب (فقط اگه نداشته باشه)
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.constants import Role
from apps.accounts.models import BusinessOwnerProfile

from .constants import Plan
from .models import Business, Staff, Station

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  بعد از ساخت Business
# ═══════════════════════════════════════════════════════════════


@receiver(post_save, sender=Business)
def on_business_created(
    sender: type[Business],
    instance: Business,
    created: bool,
    **kwargs,
) -> None:
    """
    راه‌اندازی اولیه‌ی Business.

    ─── کارها: ───
    1. آپدیت role کاربر به business_owner
    2. ساخت BusinessOwnerProfile
    3. تنظیم plan_expires_at اگه trial و خالیه
    4. ساخت Staff صاحب (اگه نداشته باشه)
    5. ساخت Station پیش‌فرض برای کسب‌وکار شخصی
    """
    if not created:
        return

    owner = instance.owner

    # ─── ۱. آپدیت role ───
    if owner.role != Role.BUSINESS_OWNER:
        owner.role = Role.BUSINESS_OWNER
        owner.save(update_fields=["role"])
        logger.info(f"Updated role for {owner.phone} to business_owner")

    # ─── ۲. BusinessOwnerProfile ───
    BusinessOwnerProfile.objects.get_or_create(user=owner)

    # ─── ۳. تنظیم trial (اگه خالیه) ───
    if instance.plan == Plan.TRIAL and not instance.plan_expires_at:
        from datetime import timedelta

        from django.utils import timezone

        instance.plan_expires_at = timezone.localdate() + timedelta(days=30)
        instance.save(update_fields=["plan_expires_at", "updated_at"])
        logger.info(f"Trial set for {instance.name}: 30 days")

    # ─── ۴. Staff صاحب ───
    owner_staff, staff_created = Staff.objects.get_or_create(
        business=instance,
        is_owner=True,
        defaults={
            "name": instance.owner_name or instance.name or owner.display_name,
            "phone": owner.phone,
        },
    )
    if staff_created:
        logger.info(f"Owner Staff created for {instance.name}")

    # ─── ۵. Station پیش‌فرض (فقط برای شخصی) ───
    if not instance.is_salon:
        station, station_created = Station.objects.get_or_create(
            business=instance,
            name="محل کار",
            defaults={
                "order": 0,
                "is_active": True,
            },
        )
        if station_created:
            logger.info(f"Default station created for {instance.name}")