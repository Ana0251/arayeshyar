"""
View داشبورد کسب‌وکار.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.booking.selectors import (
    get_business_appointments_for_date,
    get_business_stats,
    get_upcoming_appointments_for_business,
)
from apps.core.decorators import business_required


@business_required
@require_GET
def dashboard(request: HttpRequest) -> HttpResponse:
    """
    داشبورد کسب‌وکار.

    ─── نمایش: ───
    - هشدار در انتظار تأیید
    - نوبت‌های امروز
    - نوبت‌های آینده (گروه‌بندی‌شده بر اساس روز، تا ۷ روز)
    - آمار کلی
    """
    business = request.user.business
    today = timezone.localdate()

    # ─── نوبت‌های امروز ───
    appointments_today = get_business_appointments_for_date(business, today)

    # ─── نوبت‌های آینده (گروه‌بندی‌شده، از فردا تا ۷ روز) ───
    appointments_upcoming_groups = get_upcoming_appointments_for_business(
        business,
        days_ahead=7,
    )

    # ─── آمار ───
    stats = get_business_stats(business)

    # ─── تعداد کل نوبت‌های آینده ───
    upcoming_total = sum(g["count"] for g in appointments_upcoming_groups)

    return render(
        request,
        "business/dashboard.html",
        {
            "business": business,
            "appointments_today": appointments_today,
            "appointments_upcoming_groups": appointments_upcoming_groups,
            "upcoming_total": upcoming_total,
            "stats": stats,
            "today": today,
            "pending_approval": not business.is_active,
        },
    )