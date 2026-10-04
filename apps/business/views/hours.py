"""
Views مدیریت برنامه هفتگی.

─── نکته: ───
WorkingHours فقط برای کسب‌وکارهای شخصی (is_salon=False) استفاده میشه.
برای سالن‌ها، از StaffSchedule (شیفت کارمندها) استفاده کن.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import WorkingHoursForm
from ..models import WorkingHours

from ._helpers import htmx_error, htmx_response, is_htmx

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Check: فقط شخصی
# ═══════════════════════════════════════════════════════════════


def _check_not_salon(business):
    """
    اگه کسب‌وکار سالن باشه، به شیفت‌ها redirect کن.

    Returns:
        HttpResponse اگه سالن بود، وگرنه None.
    """
    if business.is_salon:
        messages.info(
            _("سالن‌ها باید از «شیفت کارمندها» استفاده کنن، نه برنامه هفتگی."),
        )
        return redirect("business:manage_staff_schedules")
    return None


# ═══════════════════════════════════════════════════════════════
#  Manage Hours
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def manage_hours(request: HttpRequest) -> HttpResponse:
    """مدیریت برنامه هفتگی (فقط شخصی)."""
    business = request.user.business

    # ─── اگه سالن باشه، redirect ───
    redirect_response = _check_not_salon(business)
    if redirect_response:
        return redirect_response

    hours = business.working_hours.filter(
        station__isnull=True
    ).order_by("weekday")

    if request.method == "POST":
        form = WorkingHoursForm(request.POST)

        if form.is_valid():
            wh = form.save(commit=False)
            wh.business = business

            if WorkingHours.objects.filter(
                business=business,
                weekday=wh.weekday,
                station__isnull=True,
            ).exists():
                if is_htmx(request):
                    return htmx_error(
                        request,
                        _("برای %(day)s قبلاً برنامه ثبت شده.")
                        % {"day": wh.get_weekday_display()},
                    )
                messages.error(
                    request,
                    _("برای %(day)s قبلاً برنامه ثبت شده.")
                    % {"day": wh.get_weekday_display()},
                )
            else:
                wh.save()

                if is_htmx(request):
                    hours = business.working_hours.filter(
                        station__isnull=True
                    ).order_by("weekday")
                    return htmx_response(
                        request,
                        template="business/partials/_hours_list.html",
                        context={
                            "hours": hours,
                            "business": business,
                        },
                    )

                messages.success(
                    request,
                    _("برنامه %(day)s ثبت شد. ✅")
                    % {"day": wh.get_weekday_display()},
                )
                return redirect("business:manage_hours")
        else:
            if is_htmx(request):
                return htmx_error(
                    request,
                    _("لطفاً خطاها رو برطرف کن."),
                )
    else:
        form = WorkingHoursForm()

    return render(
        request,
        "business/manage_hours.html",
        {
            "business": business,
            "hours": hours,
            "form": form,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Delete Working Hours
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def delete_working_hours(
    request: HttpRequest,
    hours_id: int,
) -> HttpResponse:
    """حذف برنامه هفتگی."""
    business = request.user.business

    # ─── اگه سالن باشه، redirect ───
    redirect_response = _check_not_salon(business)
    if redirect_response:
        return redirect_response

    wh = get_object_or_404(
        WorkingHours,
        id=hours_id,
        business=business,
    )

    label = wh.get_weekday_display()
    wh.delete()

    if is_htmx(request):
        hours = business.working_hours.filter(
            station__isnull=True
        ).order_by("weekday")
        return htmx_response(
            request,
            template="business/partials/_hours_list.html",
            context={
                "hours": hours,
                "business": business,
            },
        )

    messages.success(
        request,
        _("برنامه %(label)s حذف شد.") % {"label": label},
    )
    return redirect("business:manage_hours")