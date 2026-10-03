"""
Views مدیریت خدمات.

- manage_services  → لیست + افزودن
- edit_service     → ویرایش
- delete_service   → حذف
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import ServiceForm
from ..models import Business, Service, Station

from ._helpers import htmx_error, htmx_response, is_htmx

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Manage Services
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def manage_services(request: HttpRequest) -> HttpResponse:
    """
    مدیریت خدمات.

    ─── GET: ───
    نمایش لیست + فرم افزودن

    ─── POST: ───
    افزودن خدمت جدید (HTMX)
    """
    business = request.user.business

    # ─── فیلتر ایستگاه (برای سالن‌ها) ───
    station_id = request.GET.get("station")
    selected_station: Station | None = None

    if station_id and business.is_salon:
        selected_station = get_object_or_404(
            Station,
            id=station_id,
            business=business,
        )

    # ─── انتخاب ایستگاه پیش‌فرض برای شخصی ───
    default_station: Station | None = None
    if not business.is_salon:
        default_station = business.stations.filter(is_active=True).first()

    # ═══════════════════════════════════════════════════════════
    #  لیست خدمات
    #  ─── نکته: چون Service.station اجباریه (nullable نیست)،
    #           برای شخصی ایستگاه پیش‌فرض رو فیلتر می‌کنیم.
    # ═══════════════════════════════════════════════════════════
    if business.is_salon:
        if selected_station:
            services = business.services.filter(
                station=selected_station
            ).order_by("order", "name")
        else:
            # سالن بدون انتخاب ایستگاه → همه‌ی خدمات
            services = business.services.all().order_by("order", "name")
    else:
        # شخصی → خدمات ایستگاه پیش‌فرض
        if default_station:
            services = business.services.filter(
                station=default_station
            ).order_by("order", "name")
        else:
            services = business.services.none()

    # ─── POST: افزودن ───
    if request.method == "POST":
        form = ServiceForm(request.POST)

        if form.is_valid():
            svc = form.save(commit=False)
            svc.business = business

            # ─── انتخاب ایستگاه ───
            if selected_station:
                svc.station = selected_station
            elif not business.is_salon and default_station:
                svc.station = default_station
            elif business.is_salon and not selected_station:
                # سالن بدون ایستگاه انتخاب‌شده → نمی‌تونیم ذخیره کنیم
                if is_htmx(request):
                    return htmx_error(
                        request,
                        _("لطفاً اول یه ایستگاه انتخاب کن."),
                    )
                messages.error(request, _("لطفاً اول یه ایستگاه انتخاب کن."))
                # ادامه نده
                return redirect("business:manage_services")

            # ─── چک تکراری ───
            if Service.objects.filter(
                business=business,
                station=svc.station,
                name=svc.name,
            ).exists():
                if is_htmx(request):
                    return htmx_error(
                        request,
                        _("این خدمت قبلاً تعریف شده."),
                    )
                messages.error(request, _("این خدمت قبلاً تعریف شده."))
            else:
                svc.save()

                if is_htmx(request):
                    # ─── refresh لیست ───
                    if business.is_salon:
                        if selected_station:
                            services = business.services.filter(
                                station=selected_station
                            ).order_by("order", "name")
                        else:
                            services = business.services.all().order_by(
                                "order", "name"
                            )
                    else:
                        services = business.services.filter(
                            station=default_station
                        ).order_by("order", "name") if default_station else business.services.none()

                    return htmx_response(
                        request,
                        template="business/partials/_services_list.html",
                        context={
                            "services": services,
                            "business": business,
                            "station": selected_station,
                        },
                    )

                messages.success(
                    request,
                    _("خدمت «%(name)s» ثبت شد. ✅") % {"name": svc.name},
                )
                return redirect("business:manage_services")
        else:
            if is_htmx(request):
                return htmx_error(
                    request,
                    _("لطفاً خطاها رو برطرف کن."),
                )
            messages.error(request, _("لطفاً خطاها رو برطرف کن."))
    else:
        form = ServiceForm()

    return render(
        request,
        "business/manage_services.html",
        {
            "business": business,
            "services": services,
            "form": form,
            "selected_station": selected_station,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Edit Service
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def edit_service(
    request: HttpRequest,
    service_id: int,
) -> HttpResponse:
    """ویرایش خدمت."""
    business = request.user.business
    service = get_object_or_404(
        Service,
        id=service_id,
        business=business,
    )

    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)

        if form.is_valid():
            form.save()
            messages.success(request, _("خدمت به‌روزرسانی شد. ✅"))
            return redirect("business:manage_services")
    else:
        form = ServiceForm(instance=service)

    return render(
        request,
        "business/edit_service.html",
        {
            "business": business,
            "service": service,
            "form": form,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Delete Service
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def delete_service(
    request: HttpRequest,
    service_id: int,
) -> HttpResponse:
    """
    حذف خدمت.

    ─── نکته: ───
    خدمات با نوبت قابل حذف نیستن (فقط is_active=False).
    """
    business = request.user.business
    service = get_object_or_404(
        Service,
        id=service_id,
        business=business,
    )

    # ─── چک: نوبت داره؟ ───
    has_appointments = service.appointments.exclude(
        status="cancelled"
    ).exists()

    if has_appointments:
        if is_htmx(request):
            return htmx_error(
                request,
                _("این خدمت نوبت داره و قابل حذف نیست. غیرفعالش کن."),
            )
        messages.error(
            request,
            _("این خدمت نوبت داره و قابل حذف نیست. غیرفعالش کن."),
        )
        return redirect("business:manage_services")

    name = service.name
    service.delete()

    # ─── refresh لیست ───
    if is_htmx(request):
        services = business.services.filter(
            station__isnull=True
        ).order_by("order", "name")

        return htmx_response(
            request,
            template="business/partials/_services_list.html",
            context={
                "services": services,
                "business": business,
                "station": None,
            },
        )

    messages.success(
        request,
        _("خدمت «%(name)s» حذف شد.") % {"name": name},
    )
    return redirect("business:manage_services")