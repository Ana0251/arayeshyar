"""
View آمار و گزارش‌های کسب‌وکار.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

from apps.analytics.constants import AnalyticsRange
from apps.core.decorators import business_required

from ..selectors import get_analytics_data

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Mapping Range → Days
# ═══════════════════════════════════════════════════════════════

RANGE_TO_DAYS = {
    "today": 1,
    "week": 7,
    "month": 30,
    "quarter": 90,
    "year": 365,
}


# ═══════════════════════════════════════════════════════════════
#  Analytics
# ═══════════════════════════════════════════════════════════════


@business_required
@require_GET
def analytics(request: HttpRequest) -> HttpResponse:
    """
    صفحه‌ی آمار و گزارش‌ها.

    ─── Query params: ───
    - range: today / week / month / quarter / year (پیش‌فرض month)
    """
    business = request.user.business

    # ─── چک پلن ───
    if not business.has_pro_features:
        messages.warning(
            request,
            _("آمار و گزارش‌ها فقط برای پلن ویژه فعاله."),
        )
        return redirect("business:dashboard")

    # ─── بازه ───
    range_key = request.GET.get("range", "month")
    if range_key not in RANGE_TO_DAYS:
        range_key = "month"

    days = RANGE_TO_DAYS[range_key]

    # ─── داده ───
    data = get_analytics_data(business, days=days)

    # ─── context ───
    context = {
        "business": business,
        "range_key": range_key,
        "range_days": days,
        "ranges": [
            ("today", "امروز"),
            ("week", "این هفته"),
            ("month", "این ماه"),
            ("quarter", "سه ماه اخیر"),
            ("year", "سال اخیر"),
        ],
        **data,
    }

    return render(request, "business/analytics.html", context)