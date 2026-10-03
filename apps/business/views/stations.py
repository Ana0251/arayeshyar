"""
Views مدیریت ایستگاه‌ها (فقط سالن‌ها).
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import StationForm
from ..models import Station

from ._helpers import (
    check_salon_required,
    htmx_error,
    htmx_response,
    is_htmx,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Manage Stations
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def manage_stations(request: HttpRequest) -> HttpResponse:
    """مدیریت ایستگاه‌ها."""
    business = request.user.business

    # ─── فقط سالن ───
    redirect_response = check_salon_required(request, business)
    if redirect_response:
        return redirect_response

    stations = business.stations.all().order_by("order", "id")

    if request.method == "POST":
        form = StationForm(request.POST)

        if form.is_valid():
            station = form.save(commit=False)
            station.business = business

            # ─── چک تکراری ───
            if Station.objects.filter(
                business=business,
                name=station.name,
            ).exists():
                if is_htmx(request):
                    return htmx_error(
                        request,
                        _("این ایستگاه قبلاً ثبت شده."),
                    )
                messages.error(request, _("این ایستگاه قبلاً ثبت شده."))
            else:
                station.save()

                if is_htmx(request):
                    stations = business.stations.all().order_by("order", "id")
                    return htmx_response(
                        request,
                        template="business/partials/_stations_list.html",
                        context={
                            "stations": stations,
                            "business": business,
                        },
                    )

                messages.success(
                    request,
                    _("ایستگاه «%(name)s» ثبت شد. ✅")
                    % {"name": station.name},
                )
                return redirect("business:manage_stations")
        else:
            if is_htmx(request):
                return htmx_error(
                    request,
                    _("لطفاً خطاها رو برطرف کن."),
                )
    else:
        form = StationForm()

    return render(
        request,
        "business/manage_stations.html",
        {
            "business": business,
            "stations": stations,
            "form": form,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Edit Station
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def edit_station(
    request: HttpRequest,
    station_id: int,
) -> HttpResponse:
    """ویرایش ایستگاه."""
    business = request.user.business

    redirect_response = check_salon_required(request, business)
    if redirect_response:
        return redirect_response

    station = get_object_or_404(
        Station,
        id=station_id,
        business=business,
    )

    if request.method == "POST":
        form = StationForm(request.POST, instance=station)

        if form.is_valid():
            form.save()
            messages.success(request, _("ایستگاه به‌روزرسانی شد. ✅"))
            return redirect("business:manage_stations")
    else:
        form = StationForm(instance=station)

    return render(
        request,
        "business/edit_station.html",
        {
            "business": business,
            "station": station,
            "form": form,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Delete Station
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def delete_station(
    request: HttpRequest,
    station_id: int,
) -> HttpResponse:
    """حذف ایستگاه."""
    business = request.user.business

    redirect_response = check_salon_required(request, business)
    if redirect_response:
        return redirect_response

    station = get_object_or_404(
        Station,
        id=station_id,
        business=business,
    )

    # ─── چک: خدمت یا نوبت داره؟ ───
    if station.services.exists():
        if is_htmx(request):
            return htmx_error(
                request,
                _("این ایستگاه خدمت داره. اول خدماتش رو حذف کن."),
            )
        messages.error(
            request,
            _("این ایستگاه خدمت داره. اول خدماتش رو حذف کن."),
        )
        return redirect("business:manage_stations")

    name = station.name
    station.delete()

    if is_htmx(request):
        stations = business.stations.all().order_by("order", "id")
        return htmx_response(
            request,
            template="business/partials/_stations_list.html",
            context={
                "stations": stations,
                "business": business,
            },
        )

    messages.success(
        request,
        _("ایستگاه «%(name)s» حذف شد.") % {"name": name},
    )
    return redirect("business:manage_stations")