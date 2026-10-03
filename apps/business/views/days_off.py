"""
Views مدیریت روزهای تعطیل.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import DayOffForm
from ..models import DayOff

from ._helpers import htmx_error, htmx_response, is_htmx

logger = logging.getLogger(__name__)


@business_required
@require_http_methods(["GET", "POST"])
def manage_days_off(request: HttpRequest) -> HttpResponse:
    """مدیریت روزهای تعطیل."""
    business = request.user.business

    days_off = business.days_off.filter(
        station__isnull=True
    ).order_by("date")

    if request.method == "POST":
        form = DayOffForm(request.POST)

        if form.is_valid():
            day_off = form.save(commit=False)
            day_off.business = business

            # ─── چک تکراری ───
            if DayOff.objects.filter(
                business=business,
                date=day_off.date,
                station__isnull=True,
            ).exists():
                if is_htmx(request):
                    return htmx_error(
                        request,
                        _("این تاریخ قبلاً ثبت شده."),
                    )
                messages.error(request, _("این تاریخ قبلاً ثبت شده."))
            else:
                day_off.save()

                if is_htmx(request):
                    days_off = business.days_off.filter(
                        station__isnull=True
                    ).order_by("date")
                    return htmx_response(
                        request,
                        template="business/partials/_days_off_list.html",
                        context={
                            "days_off": days_off,
                            "business": business,
                        },
                    )

                messages.success(request, _("روز تعطیل ثبت شد. ✅"))
                return redirect("business:manage_days_off")
        else:
            if is_htmx(request):
                return htmx_error(
                    request,
                    _("لطفاً خطاها رو برطرف کن."),
                )
    else:
        form = DayOffForm()

    return render(
        request,
        "business/manage_days_off.html",
        {
            "business": business,
            "days_off": days_off,
            "form": form,
        },
    )


@business_required
@require_POST
def delete_day_off(
    request: HttpRequest,
    day_off_id: int,
) -> HttpResponse:
    """حذف روز تعطیل."""
    business = request.user.business
    day_off = get_object_or_404(
        DayOff,
        id=day_off_id,
        business=business,
    )
    day_off.delete()

    if is_htmx(request):
        days_off = business.days_off.filter(
            station__isnull=True
        ).order_by("date")
        return htmx_response(
            request,
            template="business/partials/_days_off_list.html",
            context={
                "days_off": days_off,
                "business": business,
            },
        )

    messages.success(request, _("روز تعطیل حذف شد."))
    return redirect("business:manage_days_off")