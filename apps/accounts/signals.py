"""
Signal های اپ accounts.

هدف: ساخت خودکار پروفایل بعد از ساخت کاربر.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import Role
from .models import BusinessOwnerProfile, CustomerProfile, User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_profile_for_user(
    sender: type[User],
    instance: User,
    created: bool,
    **kwargs,
) -> None:
    """
    ساخت خودکار پروفایل بعد از ساخت کاربر.

    ─── منطق: ───
    - role=customer        → CustomerProfile
    - role=business_owner  → BusinessOwnerProfile
    - role=admin           → بدون پروفایل
    """
    if not created:
        return

    if instance.role == Role.CUSTOMER:
        CustomerProfile.objects.get_or_create(user=instance)
        logger.debug(f"CustomerProfile created for {instance.phone}")

    elif instance.role == Role.BUSINESS_OWNER:
        BusinessOwnerProfile.objects.get_or_create(user=instance)
        logger.debug(f"BusinessOwnerProfile created for {instance.phone}")