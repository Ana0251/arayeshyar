"""
View داشبورد کسب‌وکار.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.booking.selectors import (
    get_business_appointments_for_date,
    get_business_stats,
    get_upcoming_appointments_for_business,
)
from apps.core.decorators import business_required
from django.utils import timezone


# ═══════════════════════════════════════════════════════════════
#  Dashboard
# ═══════════════════════════════════════════════════════════════


@business_required
@require_GET
def dashboard(request: HttpRequest) -> HttpResponse:
    """
    داشبورد کسب‌وکار.

    ─── نمایش: ───
    - هشدار در انتظار تأیید (اگه is_active=False)
    - نوبت‌های امروز
    - نوبت‌های آینده
    - آمار کلی
    - دسترسی سریع
    """
    business = request.user.business
    today = timezone.localdate()

    # ─── نوبت‌های امروز ───
    appointments_today = get_business_appointments_for_date(business, today)

    # ─── نوبت‌های آینده ───
    appointments_upcoming = get_upcoming_appointments_for_business(
        business,
        limit=20,
    )

    # ─── آمار ───
    stats = get_business_stats(business)

    return render(
        request,
        "business/dashboard.html",
        {
            "business": business,
            "appointments_today": appointments_today,
            "appointments_upcoming": appointments_upcoming,
            "stats": stats,
            "today": today,
            "pending_approval": not business.is_active,
        },
    )