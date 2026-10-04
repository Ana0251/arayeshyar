"""
Context Processor های سراسری.

این‌ها توی همه‌ی template ها به‌صورت خودکار در دسترسن.
"""

from typing import Any

from django.http import HttpRequest


def user_context(request: HttpRequest) -> dict[str, Any]:
    """
    اطلاعات کاربر و کسب‌وکارش رو به context اضافه می‌کنه.

    توی template ها:
        {% if user_business %}
            {{ user_business.name }}
        {% endif %}

        {% if user_customer_profile %}
            {{ user_customer_profile.full_name }}
        {% endif %}
    """
    context: dict[str, Any] = {
        "user_business": None,
        "user_customer_profile": None,
        "is_business_owner": False,
        "is_customer": False,
    }

    if not request.user.is_authenticated:
        return context

    user = request.user

    # ─── کسب‌وکار ───
    try:
        business = user.business
        context["user_business"] = business
        context["is_business_owner"] = True
    except AttributeError:
        pass

    # ─── پروفایل مشتری ───
    try:
        customer_profile = user.customer_profile
        context["user_customer_profile"] = customer_profile
        context["is_customer"] = True
    except AttributeError:
        pass

    return context


def site_context(request: HttpRequest) -> dict[str, Any]:
    """
    اطلاعات سایت رو به context اضافه می‌کنه.

    توی template ها:
        {{ site_name }}
        {{ site_domain }}
    """
    from django.conf import settings

    return {
        "site_name": getattr(settings, "SITE_NAME", "آرایشیار"),
        "site_domain": getattr(settings, "SITE_DOMAIN", "localhost"),
    }
    
def site_context(request: HttpRequest) -> dict[str, Any]:
    """اطلاعات سایت + راه‌های ارتباطی."""
    from django.conf import settings

    return {
        "site_name": getattr(settings, "SITE_NAME", "آرایشیار"),
        "site_domain": getattr(settings, "SITE_DOMAIN", "localhost"),
        "site_whatsapp": getattr(settings, "SUPPORT_WHATSAPP", ""),
        "site_telegram": getattr(settings, "SUPPORT_TELEGRAM", ""),
        "site_phone": getattr(settings, "SUPPORT_PHONE", ""),
    }