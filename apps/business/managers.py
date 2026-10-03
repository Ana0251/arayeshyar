"""
Manager های سفارشی برای اپ business.
"""

from typing import TYPE_CHECKING

from django.db import models

from .constants import ChangeRequestStatus, Plan

if TYPE_CHECKING:
    pass


class BusinessQuerySet(models.QuerySet):
    """QuerySet سفارشی برای Business."""

    def active(self) -> "BusinessQuerySet":
        """فقط کسب‌وکارهای تأییدشده."""
        return self.filter(is_active=True, is_rejected=False)

    def pending(self) -> "BusinessQuerySet":
        """فقط کسب‌وکارهای در انتظار تأیید."""
        return self.filter(is_active=False, is_rejected=False)

    def rejected(self) -> "BusinessQuerySet":
        """فقط کسب‌وکارهای ردشده."""
        return self.filter(is_rejected=True)

    def salons(self) -> "BusinessQuerySet":
        """فقط سالن‌ها."""
        return self.filter(is_salon=True)

    def individuals(self) -> "BusinessQuerySet":
        """فقط کسب‌وکارهای شخصی."""
        return self.filter(is_salon=False)

    def with_pro(self) -> "BusinessQuerySet":
        """کسب‌وکارهای با پلن ویژه."""
        return self.filter(plan=Plan.PRO)

    def with_owner(self) -> "BusinessQuerySet":
        """با owner join شده."""
        return self.select_related("owner")

    def with_activity(self) -> "BusinessQuerySet":
        """با activity_type و target_audience join شده."""
        return self.select_related("activity_type", "target_audience")


class BusinessManager(models.Manager):
    """Manager پیش‌فرض Business."""

    def get_queryset(self) -> BusinessQuerySet:
        return BusinessQuerySet(self.model, using=self._db)

    def active(self) -> BusinessQuerySet:
        return self.get_queryset().active()

    def pending(self) -> BusinessQuerySet:
        return self.get_queryset().pending()

    def rejected(self) -> BusinessQuerySet:
        return self.get_queryset().rejected()

    def salons(self) -> BusinessQuerySet:
        return self.get_queryset().salons()

    def individuals(self) -> BusinessQuerySet:
        return self.get_queryset().individuals()


class ProfileChangeRequestManager(models.Manager):
    """Manager برای ProfileChangeRequest."""

    def pending(self):
        """درخواست‌های در انتظار."""
        return self.filter(status=ChangeRequestStatus.PENDING)

    def for_business(self, business):
        """درخواست‌های یه کسب‌وکار."""
        return self.filter(business=business)


class ProfileChangeRequestManager(models.Manager):
    """Manager برای ProfileChangeRequest."""

    def pending(self):
        """درخواست‌های در انتظار."""
        return self.filter(status="pending")

    def for_business(self, business):
        """درخواست‌های یه کسب‌وکار."""
        return self.filter(business=business)