"""مدیریت کارمندهای سالن با UX ساده‌تر برای اتصال خدمت و اتاق."""

from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import StaffManagementForm
from ..models import Service, Staff, StaffService, Station


def _service_groups(business):
    stations = business.stations.filter(is_active=True).order_by("order", "name")
    services = (
        Service.objects.filter(
            business=business,
            is_active=True,
            station__is_active=True,
        )
        .select_related("station")
        .order_by("station__order", "station__name", "order", "name")
    )
    by_station = {}
    for service in services:
        by_station.setdefault(service.station_id, []).append(service)
    return [
        {"station": station, "services": by_station.get(station.id, [])}
        for station in stations
        if by_station.get(station.id)
    ]


def _selected_service_ids(form, staff=None):
    if form.is_bound:
        ids = []
        for value in form.data.getlist("services"):
            try:
                ids.append(int(value))
            except (TypeError, ValueError):
                pass
        return ids
    if staff and staff.pk:
        return list(
            StaffService.objects.filter(staff=staff, is_active=True)
            .values_list("service_id", flat=True)
        )
    return []


@transaction.atomic
def _sync_services(staff, services):
    selected = {service.id: service for service in services}
    existing = {
        rel.service_id: rel
        for rel in StaffService.objects.filter(staff=staff).select_related("service")
    }

    for service_id, service in selected.items():
        rel = existing.get(service_id)
        if rel:
            changed = False
            if rel.station_id != service.station_id:
                rel.station = service.station
                changed = True
            if not rel.is_active:
                rel.is_active = True
                changed = True
            if changed:
                rel.save(update_fields=["station", "is_active", "updated_at"])
        else:
            StaffService.objects.create(
                staff=staff,
                service=service,
                station=service.station,
                is_active=True,
            )

    StaffService.objects.filter(staff=staff).exclude(
        service_id__in=selected.keys()
    ).update(is_active=False)


@business_required
@require_http_methods(["GET", "POST"])
def manage_staff(request: HttpRequest) -> HttpResponse:
    business = request.user.business
    if not business.is_salon:
        messages.info(request, _("مدیریت کارمندها فقط برای سالن‌هاست."))
        return redirect("business:dashboard")

    if request.method == "POST":
        form = StaffManagementForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            with transaction.atomic():
                staff = form.save(commit=False)
                staff.business = business
                staff.save()
                _sync_services(staff, form.cleaned_data["services"])
            messages.success(request, _("کارمند با موفقیت اضافه شد. ✅"))
            return redirect("business:manage_staff")
    else:
        form = StaffManagementForm(business=business)

    staff_members = (
        Staff.objects.filter(business=business)
        .prefetch_related("staff_services__service__station", "schedules")
        .order_by("order", "id")
    )

    return render(
        request,
        "business/manage_staff.html",
        {
            "business": business,
            "form": form,
            "staff_members": staff_members,
            "service_groups": _service_groups(business),
            "selected_service_ids": _selected_service_ids(form),
        },
    )


@business_required
@require_http_methods(["GET", "POST"])
def edit_staff(request: HttpRequest, staff_id: int) -> HttpResponse:
    business = request.user.business
    staff = get_object_or_404(Staff, id=staff_id, business=business)

    if request.method == "POST":
        form = StaffManagementForm(
            request.POST,
            request.FILES,
            instance=staff,
            business=business,
        )
        if form.is_valid():
            updated = form.save(commit=False)
            if staff.is_owner:
                updated.is_active = True
            with transaction.atomic():
                updated.save()
                _sync_services(updated, form.cleaned_data["services"])
            messages.success(request, _("اطلاعات کارمند به‌روزرسانی شد. ✅"))
            return redirect("business:manage_staff")
    else:
        form = StaffManagementForm(instance=staff, business=business)

    return render(
        request,
        "business/edit_staff.html",
        {
            "business": business,
            "staff": staff,
            "form": form,
            "service_groups": _service_groups(business),
            "selected_service_ids": _selected_service_ids(form, staff),
        },
    )


@business_required
@require_POST
def toggle_staff(request: HttpRequest, staff_id: int) -> HttpResponse:
    business = request.user.business
    staff = get_object_or_404(Staff, id=staff_id, business=business)
    if staff.is_owner:
        messages.warning(request, _("صاحب کسب‌وکار را نمی‌توان غیرفعال کرد."))
        return redirect("business:manage_staff")

    staff.is_active = not staff.is_active
    staff.save(update_fields=["is_active", "updated_at"])
    if staff.is_active:
        messages.success(request, _("کارمند فعال شد."))
    else:
        messages.info(request, _("کارمند غیرفعال شد؛ سوابق و نوبت‌های قبلی حفظ می‌شوند."))
    return redirect("business:manage_staff")
