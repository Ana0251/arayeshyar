"""صفحه آرایشگرها و سالن‌های ذخیره‌شده مشتری + جست‌وجو با موبایل."""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from apps.business.models import Business
from apps.core.decorators import customer_required
from apps.core.utils.phone import normalize_phone

from .models import CustomerBusiness
from .services import CustomerBusinessService

logger = logging.getLogger(__name__)


@customer_required
@require_GET
def my_businesses(request: HttpRequest) -> HttpResponse:
    customer = request.user
    relations = (
        CustomerBusiness.objects.filter(customer=customer, business__is_active=True)
        .select_related("business", "business__activity_type", "business__owner")
        .order_by("-is_favorite", "-updated_at")
    )

    query = (request.GET.get("q") or "").strip()
    search_result = None
    search_error = ""
    search_is_saved = False

    if query:
        phone = normalize_phone(query)
        if not phone:
            search_error = _("شماره موبایل معتبر وارد کن؛ مثلاً 09123456789")
        else:
            search_result = (
                Business.objects.filter(
                    owner__phone=phone,
                    is_active=True,
                    is_rejected=False,
                )
                .select_related("activity_type", "owner")
                .first()
            )
            if not search_result:
                search_error = _("آرایشگر یا سالن فعالی با این شماره پیدا نشد.")
            else:
                search_is_saved = CustomerBusiness.objects.filter(
                    customer=customer,
                    business=search_result,
                ).exists()

    return render(
        request,
        "customers/my_businesses.html",
        {
            "relations": relations,
            "query": query,
            "search_result": search_result,
            "search_error": search_error,
            "search_is_saved": search_is_saved,
        },
    )


@customer_required
@require_POST
def add_business(request: HttpRequest, business_id: int) -> HttpResponse:
    customer = request.user
    business = get_object_or_404(
        Business,
        id=business_id,
        is_active=True,
        is_rejected=False,
    )
    relation, created = CustomerBusinessService.add_to_my_list(customer, business)
    if not relation.is_favorite:
        relation.is_favorite = True
        relation.save(update_fields=["is_favorite", "updated_at"])

    if created:
        messages.success(request, _("«%(name)s» به لیستت اضافه شد. ⭐") % {"name": business.name})
    else:
        messages.info(request, _("«%(name)s» از قبل توی لیستت بود.") % {"name": business.name})
    return redirect("customers:my_businesses")


@customer_required
@require_POST
def remove_business(request: HttpRequest, business_id: int) -> HttpResponse:
    customer = request.user
    business = get_object_or_404(Business, id=business_id)
    deleted = CustomerBusinessService.remove_from_my_list(customer, business)
    if deleted:
        messages.success(request, _("«%(name)s» از لیستت حذف شد.") % {"name": business.name})
    else:
        messages.warning(request, _("این مورد توی لیستت نبود."))
    if request.headers.get("HX-Request"):
        return HttpResponse("")
    return redirect("customers:my_businesses")


@customer_required
@require_POST
def toggle_favorite(request: HttpRequest, business_id: int) -> HttpResponse:
    customer = request.user
    business = get_object_or_404(Business, id=business_id)
    relation = CustomerBusinessService.toggle_favorite(customer, business)
    if relation.is_favorite:
        messages.success(request, _("«%(name)s» به علاقه‌مندی‌ها اضافه شد. ⭐") % {"name": business.name})
    else:
        messages.info(request, _("«%(name)s» از علاقه‌مندی‌ها خارج شد.") % {"name": business.name})
    return redirect("customers:my_businesses")
