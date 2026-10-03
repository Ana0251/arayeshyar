"""
Signal های اپ business.

هدف:
- ساخت خودکار BusinessOwnerProfile بعد از ساخت Business
- ساخت خودکار Station و Staff برای کسب‌وکار شخصی
- ساخت خودکار Staff برای صاحب کسب‌وکار (سالن)
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.constants import Role
from apps.accounts.models import BusinessOwnerProfile

from .models import Business, Staff, Station

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ۱. ساخت BusinessOwnerProfile
# ═══════════════════════════════════════════════════════════════


@receiver(post_save, sender=Business)
def ensure_owner_profile(
    sender: type[Business],
    instance: Business,
    created: bool,
    **kwargs,
) -> None:
    """ساخت BusinessOwnerProfile + آپدیت role کاربر."""
    if not created:
        return

    owner = instance.owner

    # ─── آپدیت role ───
    if owner.role != Role.BUSINESS_OWNER:
        owner.role = Role.BUSINESS_OWNER
        owner.save(update_fields=["role"])
        logger.info(f"Updated role for {owner.phone} to business_owner")

    # ─── ساخت BusinessOwnerProfile ───
    BusinessOwnerProfile.objects.get_or_create(user=owner)


# ═══════════════════════════════════════════════════════════════
#  ۲. ساخت Station و Staff اولیه
# ═══════════════════════════════════════════════════════════════


@receiver(post_save, sender=Business)
def create_default_station_and_staff(
    sender: type[Business],
    instance: Business,
    created: bool,
    **kwargs,
) -> None:
    """
    ساخت Station و Staff اولیه.

    ─── منطق: ───
    - برای کسب‌وکار شخصی: یه Station («محل کار») + یه Staff (صاحب)
    - برای سالن: یه Staff (صاحب، is_owner=True)
                  کاربر باید اتاق‌ها رو خودش اضافه کنه
    """
    if not created:
        return

    owner = instance.owner

    # ─── ساخت Staff برای صاحب ───
    owner_staff, _ = Staff.objects.get_or_create(
        business=instance,
        is_owner=True,
        defaults={
            "name": instance.owner_name or instance.name or owner.display_name,
            "phone": owner.phone,
        },
    )
    logger.info(f"Owner Staff created for {instance.name}")

    # ─── ساخت Station خودکار برای شخصی ───
    if not instance.is_salon:
        Station.objects.get_or_create(
            business=instance,
            name="محل کار",
            defaults={
                "order": 0,
                "is_active": True,
            },
        )
        logger.info(f"Default station created for personal business {instance.name}")