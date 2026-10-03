"""
سرویس‌های customers.
"""

import logging

from apps.accounts.models import User
from apps.business.models import Business

from .models import CustomerBusiness

logger = logging.getLogger(__name__)


class CustomerBusinessService:
    """
    سرویس مدیریت ارتباط مشتری و کسب‌وکار.
    """

    @staticmethod
    def add_to_my_list(
        customer: User,
        business: Business,
    ) -> tuple[CustomerBusiness, bool]:
        """
        اضافه کردن کسب‌وکار به لیست مشتری.

        Returns:
            (CustomerBusiness, created)
        """
        relation, created = CustomerBusiness.objects.get_or_create(
            customer=customer,
            business=business,
        )

        if created:
            logger.info(
                f"Customer {customer.phone} added business {business.name}"
            )

        return relation, created

    @staticmethod
    def remove_from_my_list(
        customer: User,
        business: Business,
    ) -> int:
        """
        حذف کسب‌وکار از لیست مشتری.

        Returns:
            تعداد حذف‌شده (0 یا 1)
        """
        deleted, _ = CustomerBusiness.objects.filter(
            customer=customer,
            business=business,
        ).delete()

        if deleted:
            logger.info(
                f"Customer {customer.phone} removed business {business.name}"
            )

        return deleted

    @staticmethod
    def record_visit(
        customer: User,
        business: Business,
        at=None,
    ) -> CustomerBusiness:
        """
        ثبت بازدید مشتری.

        ─── خودکار: ───
        - اگه رابطه نبود، ساخته میشه
        - first_visit_at, last_visit_at, visits_count آپدیت میشن
        """
        relation, _created = CustomerBusiness.objects.get_or_create(
            customer=customer,
            business=business,
        )
        relation.record_visit(at=at)
        return relation

    @staticmethod
    def toggle_favorite(
        customer: User,
        business: Business,
    ) -> CustomerBusiness:
        """تغییر وضعیت علاقه‌مندی."""
        relation, _created = CustomerBusiness.objects.get_or_create(
            customer=customer,
            business=business,
        )
        relation.is_favorite = not relation.is_favorite
        relation.save(update_fields=["is_favorite", "updated_at"])
        return relation