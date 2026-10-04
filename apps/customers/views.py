"""
Views اپ customers.

- my_businesses → لیست کسب‌وکارهای مشتری
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from apps.business.models import Business
from apps.core.decorators import customer_required

from .models import CustomerBusiness
from .selectors import get_customer_businesses
from .services import CustomerBusinessService

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  My Businesses
# ═══════════════════════════════════════════════════════════════


@customer_required
@require_GET
def my_businesses(request: HttpRequest) -> HttpResponse:
    """
    لیست کسب‌وکارهای مشتری.

    ─── منطق: ───
    همه‌ی کسب‌وکارهایی که مشتری ازشون نوبت گرفته یا
    به‌صورت دستی اضافه کرده.
    """
    customer = request.user

    businesses = get_customer_businesses(customer)

    return render(
        request,
        "customers/my_businesses.html",
        {
            "businesses": businesses,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Remove Business
# ═══════════════════════════════════════════════════════════════


@customer_required
@require_POST
def remove_business(
    request: HttpRequest,
    business_id: int,
) -> HttpResponse:
    """حذف کسب‌وکار از لیست مشتری."""
    customer = request.user
    business = get_object_or_404(Business, id=business_id)

    deleted = CustomerBusinessService.remove_from_my_list(customer, business)

    if deleted:
        messages.success(
            request,
            _("«%(name)s» از لیستت حذف شد.") % {"name": business.name},
        )
    else:
        messages.warning(request, _("این کسب‌وکار توی لیستت نبود."))

    # ─── HTMX: حذف از DOM ───
    if request.headers.get("HX-Request"):
        return HttpResponse("")

    return redirect("customers:my_businesses")


# ═══════════════════════════════════════════════════════════════
#  Toggle Favorite
# ═══════════════════════════════════════════════════════════════


@customer_required
@require_POST
def toggle_favorite(
    request: HttpRequest,
    business_id: int,
) -> HttpResponse:
    """تغییر وضعیت علاقه‌مندی."""
    customer = request.user
    business = get_object_or_404(Business, id=business_id)

    relation = CustomerBusinessService.toggle_favorite(customer, business)

    if relation.is_favorite:
        messages.success(
            request,
            _("«%(name)s» به علاقه‌مندی‌ها اضافه شد. ⭐")
            % {"name": business.name},
        )
    else:
        messages.info(
            request,
            _("«%(name)s» از علاقه‌مندی‌ها حذف شد.")
            % {"name": business.name},
        )

    return redirect("customers:my_businesses")