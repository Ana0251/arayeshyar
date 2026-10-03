"""
Signal های customers.

هدف: وقتی مشتری اولین نوبت رو گرفت، خودکار به لیستش اضافه بشه.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.booking.models import Appointment

from .models import CustomerBusiness

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Appointment)
def auto_add_to_customer_list(
    sender: type[Appointment],
    instance: Appointment,
    created: bool,
    **kwargs,
) -> None:
    """
    وقتی نوبت جدید ساخته شد، مشتری رو به لیست کسب‌وکار اضافه کن.

    ─── فقط برای نوبت‌های جدید (نه آپدیت) ───
    """
    if not created:
        return

    CustomerBusiness.objects.get_or_create(
        customer=instance.customer,
        business=instance.business,
    )
    logger.debug(
        f"Auto-added {instance.customer.phone} to {instance.business.name}'s customers"
    )