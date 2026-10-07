"""
Views مدیریت خدمات.

- manage_services  → لیست + افزودن
- edit_service     → ویرایش + مدیریت کارمندها
- delete_service   → حذف
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import ServiceForm, StaffServiceForm
from ..models import Business, Service, StaffService, Station

from ._helpers import htmx_error, htmx_response, is_htmx

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Manage Services
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def manage_services(request: HttpRequest) -> HttpResponse:
    """مدیریت خدمات."""
    business = request.user.business

    # ─── فیلتر ایستگاه ───
    station_id = request.GET.get("station")
    selected_station: Station | None = None

    if station_id and business.is_salon:
        selected_station = get_object_or_404(
            Station,
            id=station_id,
            business=business,
        )

    # ─── ایستگاه پیش‌فرض برای شخصی ───
    default_station: Station | None = None
    if not business.is_salon:
        default_station = business.stations.filter(is_active=True).first()

    # ─── لیست خدمات ───
    if business.is_salon:
        if selected_station:
            services = business.services.filter(
                station=selected_station
            ).order_by("order", "name")
        else:
            services = business.services.all().order_by("order", "name")
    else:
        if default_station:
            services = business.services.filter(
                station=default_station
            ).order_by("order", "name")
        else:
            services = business.services.none()

    # ─── POST: افزودن ───
    if request.method == "POST":
        form = ServiceForm(
            request.POST,
            business=business,
            show_station=business.is_salon,
        )

        if form.is_valid():
            svc = form.save(commit=False)
            svc.business = business

            if business.is_salon:
                # برای سالن، اتاق مستقیماً از فرم انتخاب می‌شود.
                # این کار وابستگی ثبت خدمت به فیلتر GET بالای صفحه را حذف می‌کند.
                svc.station = form.cleaned_data["station"]
            elif default_station:
                svc.station = default_station
            else:
                if is_htmx(request):
                    return htmx_error(request, _("برای ثبت خدمت، ابتدا محل کار را ایجاد کن."))
                messages.error(request, _("برای ثبت خدمت، ابتدا محل کار را ایجاد کن."))
                return redirect("business:manage_stations")

            if Service.objects.filter(
                business=business,
                station=svc.station,
                name=svc.name,
            ).exists():
                if is_htmx(request):
                    return htmx_error(request, _("این خدمت قبلاً تعریف شده."))
                messages.error(request, _("این خدمت قبلاً تعریف شده."))
            else:
                svc.save()

                if is_htmx(request):
                    if business.is_salon:
                        if selected_station:
                            services = business.services.filter(
                                station=selected_station
                            ).order_by("order", "name")
                        else:
                            services = business.services.all().order_by("order", "name")
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
                return htmx_error(request, _("لطفاً خطاها رو برطرف کن."))
            messages.error(request, _("لطفاً خطاها رو برطرف کن."))
    else:
        form = ServiceForm(
            business=business,
            show_station=business.is_salon,
        )

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
#  Edit Service (with Staff Services)
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def edit_service(
    request: HttpRequest,
    service_id: int,
) -> HttpResponse:
    """
    ویرایش خدمت + مدیریت کارمندها.

    ─── GET: ───
    نمایش فرم + لیست کارمندها

    ─── POST: ───
    - action=update: ویرایش خدمت
    - action=add_staff: افزودن کارمند
    - action=update_staff: ویرایش قیمت کارمند
    - action=remove_staff: حذف کارمند
    """
    business = request.user.business
    service = get_object_or_404(
        Service,
        id=service_id,
        business=business,
    )

    # ═══════════════════════════════════════════════════════════
    #  POST
    # ═══════════════════════════════════════════════════════════
    if request.method == "POST":
        action = request.POST.get("action", "update")

        # ─── افزودن کارمند ───
        if action == "add_staff":
            form = StaffServiceForm(
                request.POST,
                business=business,
                station=service.station,
                service=service,
            )

            if form.is_valid():
                ss = form.save(commit=False)
                ss.station = service.station
                ss.service = service

                if StaffService.objects.filter(
                    staff=ss.staff,
                    service=service,
                    station=service.station,
                ).exists():
                    messages.warning(
                        request,
                        _("این کارمند قبلاً به این خدمت اضافه شده."),
                    )
                else:
                    ss.save()
                    messages.success(
                        request,
                        _("%(name)s به این خدمت اضافه شد. ✅")
                        % {"name": ss.staff.name},
                    )
            else:
                messages.error(request, _("لطفاً خطاها رو برطرف کن."))

            return redirect("business:edit_service", service_id=service.id)

        # ─── ویرایش قیمت کارمند ───
        elif action == "update_staff":
            staff_service_id = request.POST.get("staff_service_id")
            new_price = request.POST.get("price", "0")
            is_active = request.POST.get("is_active") == "on"

            ss = get_object_or_404(
                StaffService,
                id=staff_service_id,
                service=service,
            )

            try:
                new_price = int(new_price)
                if new_price < 0:
                    new_price = 0
            except (ValueError, TypeError):
                new_price = 0

            ss.price = new_price
            ss.is_active = is_active
            ss.save(update_fields=["price", "is_active", "updated_at"])

            messages.success(
                request,
                _("قیمت %(name)s به‌روزرسانی شد. ✅")
                % {"name": ss.staff.name},
            )
            return redirect("business:edit_service", service_id=service.id)

        # ─── حذف کارمند ───
        elif action == "remove_staff":
            staff_service_id = request.POST.get("staff_service_id")
            ss = get_object_or_404(
                StaffService,
                id=staff_service_id,
                service=service,
            )
            staff_name = ss.staff.name
            ss.delete()
            messages.success(
                request,
                _("%(name)s از این خدمت حذف شد.") % {"name": staff_name},
            )
            return redirect("business:edit_service", service_id=service.id)

        # ─── ویرایش خدمت ───
        else:
            form = ServiceForm(
                request.POST,
                instance=service,
                business=business,
                show_station=False,
            )

            if form.is_valid():
                form.save()
                messages.success(request, _("خدمت به‌روزرسانی شد. ✅"))
                return redirect("business:manage_services")
    else:
        form = ServiceForm(
            instance=service,
            business=business,
            show_station=False,
        )

    # ═══════════════════════════════════════════════════════════
    #  GET
    # ═══════════════════════════════════════════════════════════
    staff_service_form = StaffServiceForm(
        business=business,
        station=service.station,
        service=service,
    )

    staff_services = (
        StaffService.objects.filter(service=service)
        .select_related("staff")
        .order_by("staff__order", "staff__name")
    )

    return render(
        request,
        "business/edit_service.html",
        {
            "business": business,
            "service": service,
            "form": form,
            "staff_service_form": staff_service_form,
            "staff_services": staff_services,
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
    """حذف خدمت."""
    business = request.user.business
    service = get_object_or_404(
        Service,
        id=service_id,
        business=business,
    )

    has_appointments = service.appointments.exclude(status="cancelled").exists()

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

    if is_htmx(request):
        services = business.services.filter(
            station__isnull=False
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