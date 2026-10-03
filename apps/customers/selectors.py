"""
Selectors — کوئری‌های خواندنی customers.
"""

from django.db.models import QuerySet

from apps.accounts.models import User
from apps.business.models import Business

from .models import CustomerBusiness


def get_customer_businesses(customer: User) -> QuerySet[Business]:
    """
    کسب‌وکارهای یه مشتری.

    فقط کسب‌وکارهای فعال (is_active=True).
    """
    return (
        Business.objects.filter(
            my_customers__customer=customer,
            is_active=True,
        )
        .distinct()
        .order_by("-my_customers__created_at")
    )


def get_business_customers(business: Business) -> QuerySet[User]:
    """
    مشتری‌های یه کسب‌وکار.

    فقط مشتری‌های فعال (is_active=True).
    """
    return (
        User.objects.filter(
            my_businesses__business=business,
            is_active=True,
            role="customer",
        )
        .distinct()
        .order_by("-my_businesses__created_at")
    )


def is_customer_of_business(customer: User, business: Business) -> bool:
    """آیا این مشتری، مشتری این کسب‌وکاره؟"""
    return CustomerBusiness.objects.filter(
        customer=customer,
        business=business,
    ).exists()


def get_customer_business_relation(
    customer: User,
    business: Business,
) -> CustomerBusiness | None:
    """گرفتن رابطه‌ی مشتری و کسب‌وکار."""
    try:
        return CustomerBusiness.objects.get(
            customer=customer,
            business=business,
        )
    except CustomerBusiness.DoesNotExist:
        return None