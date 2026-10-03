"""
Views مدیریت ساعات خاص.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import SpecialWorkingHoursForm
from ..models import SpecialWorkingHours

from ._helpers import htmx_error, htmx_response, is_htmx

logger = logging.getLogger(__name__)


@business_required
@require_http_methods(["GET", "POST"])
def manage_special_hours(request: HttpRequest) -> HttpResponse:
    """مدیریت ساعات خاص."""
    business = request.user.business

    specials = business.special_hours.filter(
        station__isnull=True
    ).order_by("date")

    if request.method == "POST":
        form = SpecialWorkingHoursForm(request.POST)

        if form.is_valid():
            sp = form.save(commit=False)
            sp.business = business

            if SpecialWorkingHours.objects.filter(
                business=business,
                date=sp.date,
                station__isnull=True,
            ).exists():
                if is_htmx(request):
                    return htmx_error(
                        request,
                        _("برای این تاریخ قبلاً ثبت شده."),
                    )
                messages.error(
                    request,
                    _("برای این تاریخ قبلاً ثبت شده."),
                )
            else:
                sp.save()

                if is_htmx(request):
                    specials = business.special_hours.filter(
                        station__isnull=True
                    ).order_by("date")
                    return htmx_response(
                        request,
                        template="business/partials/_special_hours_list.html",
                        context={
                            "specials": specials,
                            "business": business,
                        },
                    )

                messages.success(request, _("ساعت خاص ثبت شد. ✅"))
                return redirect("business:manage_special_hours")
        else:
            if is_htmx(request):
                return htmx_error(
                    request,
                    _("لطفاً خطاها رو برطرف کن."),
                )
    else:
        form = SpecialWorkingHoursForm()

    return render(
        request,
        "business/manage_special_hours.html",
        {
            "business": business,
            "specials": specials,
            "form": form,
        },
    )


@business_required
@require_POST
def delete_special_hours(
    request: HttpRequest,
    special_id: int,
) -> HttpResponse:
    """حذف ساعت خاص."""
    business = request.user.business
    sp = get_object_or_404(
        SpecialWorkingHours,
        id=special_id,
        business=business,
    )
    sp.delete()

    if is_htmx(request):
        specials = business.special_hours.filter(
            station__isnull=True
        ).order_by("date")
        return htmx_response(
            request,
            template="business/partials/_special_hours_list.html",
            context={
                "specials": specials,
                "business": business,
            },
        )

    messages.success(request, _("ساعت خاص حذف شد."))
    return redirect("business:manage_special_hours")