"""
Selectors — کوئری‌های خواندنی business.
"""

from typing import TYPE_CHECKING

from django.db.models import Count, Prefetch, Q, QuerySet

from .models import (
    Business,
    DayOff,
    Service,
    SpecialWorkingHours,
    Station,
    WorkingHours,
)

if TYPE_CHECKING:
    from apps.accounts.models import User


# ═══════════════════════════════════════════════════════════════
#  Public
# ═══════════════════════════════════════════════════════════════


def get_active_businesses() -> QuerySet[Business]:
    """کسب‌وکارهای فعال."""
    return (
        Business.objects.active()
        .with_owner()
        .with_activity()
        .order_by("-created_at")
    )


def get_business_by_slug(slug: str) -> Business | None:
    """کسب‌وکار با slug (فقط فعال)."""
    return (
        Business.objects.active()
        .with_owner()
        .with_activity()
        .filter(slug=slug)
        .first()
    )


def search_businesses(
    *,
    query: str = "",
    region: str = "",
    exclude_ids: list[int] | None = None,
) -> QuerySet[Business]:
    """
    جستجوی کسب‌وکار.

    Args:
        query: جستجو در نام، آدرس، bio
        region: فیلتر منطقه
        exclude_ids: کسب‌وکارهایی که نباید نمایش داده بشن
    """
    qs = Business.objects.active().with_activity()

    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(region__icontains=query)
            | Q(address__icontains=query)
            | Q(bio__icontains=query)
        )

    if region:
        qs = qs.filter(region=region)

    if exclude_ids:
        qs = qs.exclude(id__in=exclude_ids)

    return qs.order_by("-created_at")


def get_all_regions() -> list[str]:
    """لیست مناطق یکتا (برای فیلتر)."""
    return list(
        Business.objects.active()
        .exclude(region="")
        .values_list("region", flat=True)
        .distinct()
        .order_by("region")
    )


def get_public_business_data(business: Business) -> dict:
    """
    داده‌ی کامل برای صفحه‌ی پروفایل عمومی.

    ─── نکته: ───
    از prefetch_related برای جلوگیری از N+1 استفاده می‌کنیم.
    """
    # ─── خدمات + ایستگاه‌ها ───
    services = (
        business.services.filter(is_active=True)
        .select_related("station")
        .order_by("order", "name")
    )
    stations = (
        business.stations.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "services",
                queryset=Service.objects.filter(is_active=True).order_by(
                    "order", "name"
                ),
            )
        )
        .order_by("order")
    )

    # ─── اعضای تیم فعال ───
    staff_members = (
        business.staff.filter(is_active=True)
        .prefetch_related("staff_services__service", "staff_services__station")
        .order_by("order", "id")
    )

    # ─── برنامه هفتگی ───
    working_hours = (
        business.working_hours.filter(
            is_active=True,
            station__isnull=True,
        ).order_by("weekday")
    )

    # ─── روزهای تعطیل آینده ───
    from django.utils import timezone

    upcoming_days_off = business.days_off.filter(
        date__gte=timezone.localdate(),
        station__isnull=True,
    ).order_by("date")[:5]

    return {
        "business": business,
        "services": services,
        "stations": stations,
        "staff_members": staff_members,
        "working_hours": working_hours,
        "upcoming_days_off": upcoming_days_off,
    }


# ═══════════════════════════════════════════════════════════════
#  Dashboard
# ═══════════════════════════════════════════════════════════════


def get_dashboard_data(business: Business) -> dict:
    """
    داده‌ی داشبورد.

    ─── بهینه‌سازی: ───
    از annotations برای شمارش‌ها استفاده می‌کنیم.
    """
    from apps.booking.selectors import get_business_stats

    stats = get_business_stats(business)

    return {
        "business": business,
        "stats": stats,
    }


# ═══════════════════════════════════════════════════════════════
#  Profile
# ═══════════════════════════════════════════════════════════════


def get_pending_change_requests(business: Business):
    """درخواست‌های تغییر معلق."""
    return business.change_requests.pending().order_by("-created_at")


def get_all_change_requests(
    business: Business,
    status: str | None = None,
):
    """همه‌ی درخواست‌های تغییر (با فیلتر وضعیت)."""
    qs = business.change_requests.all().order_by("-created_at")

    if status:
        qs = qs.filter(status=status)

    return qs

def get_analytics_data(
    business,
    days: int = 30,
) -> dict:
    """
    داده‌ی کامل آمار برای یه کسب‌وکار.

    ─── شامل: ───
    - overall: آمار کلی
    - golden_hours: ساعات طلایی
    - golden_weekdays: روزهای طلایی
    - service_stats: خدمات برتر
    - top_customers: مشتریان برتر
    - revenue_by_day: درآمد روزانه

    Args:
        business: کسب‌وکار
        days: بازه‌ی روز (پیش‌فرض ۳۰)
    """
    from apps.analytics.selectors import (
        get_customer_stats,
        get_golden_hours,
        get_golden_weekdays,
        get_overall_stats,
        get_revenue_by_day,
        get_service_stats,
    )

    return {
        "overall": get_overall_stats(business, days=days),
        "golden_hours": get_golden_hours(business, days=days),
        "golden_weekdays": get_golden_weekdays(business, days=days),
        "service_stats": get_service_stats(business, days=days),
        "top_customers": get_customer_stats(business, days=days),
        "revenue_by_day": get_revenue_by_day(business, days=days),
        "days": days,
    }