"""
Views مدیریت شیفت‌های کارمند.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import StaffScheduleForm
from ..models import StaffSchedule, Station


# ═══════════════════════════════════════════════════════════════
#  Helper — بررسی کسب‌وکار سالن
# ═══════════════════════════════════════════════════════════════


def _check_salon(business):
    """اگه کسب‌وکار سالن نیست، پیام بده و redirect کن."""
    if not business.is_salon:
        return redirect("business:dashboard")
    return None


# ═══════════════════════════════════════════════════════════════
#  Manage Staff Schedules
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def manage_staff_schedules(request: HttpRequest) -> HttpResponse:
    """
    مدیریت شیفت‌های کارمندها.

    ─── Query params: ───
    - station: انتخاب اتاق (اجباری)
    """
    business = request.user.business

    # ─── فقط سالن ───
    if not business.is_salon:
        messages.warning(request, _("این بخش فقط برای سالن‌هاست."))
        return redirect("business:dashboard")

    # ─── لیست اتاق‌ها ───
    stations = list(
        business.stations.filter(is_active=True).order_by("order", "id")
    )

    if not stations:
        messages.warning(
            request,
            _("اول باید یه اتاق تعریف کنی."),
        )
        return redirect("business:manage_stations")

    # ─── اتاق انتخاب‌شده ───
    station_id = request.GET.get("station") or request.POST.get("station")
    selected_station = None
    if station_id:
        selected_station = Station.objects.filter(
            id=station_id,
            business=business,
            is_active=True,
        ).first()

    # ─── اگه اتاقی انتخاب نشده، اولین اتاق ───
    if not selected_station and stations:
        selected_station = stations[0]

    # ─── POST: افزودن ───
    if request.method == "POST":
        form = StaffScheduleForm(
            request.POST,
            business=business,
            station=selected_station,
        )

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.station = selected_station

            # ─── چک تداخل ───
            conflict = StaffSchedule.objects.filter(
                staff=schedule.staff,
                station=selected_station,
                weekday=schedule.weekday,
                is_active=True,
                start_time__lt=schedule.end_time,
                end_time__gt=schedule.start_time,
            ).exclude(pk=schedule.pk).exists()

            if conflict:
                messages.error(
                    request,
                    _("این شیفت با یه شیفت دیگه تداخل داره."),
                )
            else:
                schedule.save()
                messages.success(request, _("شیفت ثبت شد. ✅"))
                return redirect(
                    f"{request.path}?station={selected_station.id}"
                )
    else:
        form = StaffScheduleForm(
            business=business,
            station=selected_station,
        )

    # ─── لیست شیفت‌ها ───
    schedules = (
        StaffSchedule.objects.filter(
            station=selected_station,
        )
        .select_related("staff", "station")
        .order_by("weekday", "start_time")
    )

    context = {
        "business": business,
        "stations": stations,
        "selected_station": selected_station,
        "schedules": schedules,
        "form": form,
    }

    return render(request, "business/manage_staff_schedules.html", context)


# ═══════════════════════════════════════════════════════════════
#  Delete Staff Schedule
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def delete_staff_schedule(
    request: HttpRequest,
    schedule_id: int,
) -> HttpResponse:
    """حذف شیفت کارمند."""
    business = request.user.business

    schedule = get_object_or_404(
        StaffSchedule,
        id=schedule_id,
        staff__business=business,
    )

    station_id = schedule.station_id
    schedule.delete()

    messages.success(request, _("شیفت حذف شد."))

    return redirect(f"/business/staff-schedules/?station={station_id}")

# ═══════════════════════════════════════════════════════════════
#  Edit Staff Schedule
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def edit_staff_schedule(
    request: HttpRequest,
    schedule_id: int,
) -> HttpResponse:
    """
    ویرایش شیفت کارمند.

    ─── چرا؟ ───
    صاحب سالن می‌تونه ساعت شیفت رو عوض کنه (مثلاً ۹-۱۴ به ۱۰-۱۵).
    """
    business = request.user.business

    if not business.is_salon:
        messages.warning(request, _("این بخش فقط برای سالن‌هاست."))
        return redirect("business:dashboard")

    schedule = get_object_or_404(
        StaffSchedule,
        id=schedule_id,
        staff__business=business,
    )

    if request.method == "POST":
        form = StaffScheduleForm(
            request.POST,
            instance=schedule,
            business=business,
            station=schedule.station,
        )

        if form.is_valid():
            updated = form.save(commit=False)

            # ─── چک تداخل ───
            conflict = StaffSchedule.objects.filter(
                staff=updated.staff,
                station=schedule.station,
                weekday=updated.weekday,
                is_active=True,
                start_time__lt=updated.end_time,
                end_time__gt=updated.start_time,
            ).exclude(pk=schedule.pk).exists()

            if conflict:
                messages.error(
                    request,
                    _("این شیفت با یه شیفت دیگه تداخل داره."),
                )
            else:
                updated.station = schedule.station  # حفظ اتاق
                updated.save()
                messages.success(request, _("شیفت به‌روزرسانی شد. ✅"))
                return redirect(
                    f"/business/staff-schedules/?station={schedule.station_id}"
                )
    else:
        form = StaffScheduleForm(
            instance=schedule,
            business=business,
            station=schedule.station,
        )

    return render(
        request,
        "business/edit_staff_schedule.html",
        {
            "business": business,
            "schedule": schedule,
            "form": form,
        },
    )