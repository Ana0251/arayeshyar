"""
Selectors — کوئری‌های خواندنی.

الگو: Selector Pattern
- کوئری‌های خواندنی اینجا
- منطق نوشتنی توی services/
- ویوها نازک می‌مونن
"""

from datetime import date, datetime

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.accounts.models import User
from apps.business.models import Business, Service, Station

from .constants import AppointmentStatus, WaitingStatus
from .models import Appointment, BlockedCustomer, WaitingList


# ═══════════════════════════════════════════════════════════════
#  Appointment
# ═══════════════════════════════════════════════════════════════


def get_business_appointments_for_date(
    business: Business,
    target_date: date,
    station: Station | None = None,
) -> QuerySet[Appointment]:
    """
    نوبت‌های یه کسب‌وکار برای یه تاریخ.

    Args:
        business: کسب‌وکار
        target_date: تاریخ
        station: (اختیاری) اگه مشخص بشه، فقط نوبت‌های اون ایستگاه
    """
    qs = (
        Appointment.objects.for_business(business)
        .for_date(target_date)
        .exclude(status=AppointmentStatus.CANCELLED)
        .with_relations()
        .order_by("start_at")
    )

    if station:
        qs = qs.filter(station=station)

    return qs


def get_customer_appointments(
    customer: User,
    *,
    upcoming_only: bool = False,
) -> QuerySet[Appointment]:
    """نوبت‌های یه مشتری."""
    qs = (
        Appointment.objects.for_customer(customer)
        .with_relations()
        .order_by("-start_at")
    )

    if upcoming_only:
        qs = qs.filter(start_at__gte=timezone.now()).exclude(
            status=AppointmentStatus.CANCELLED
        )

    return qs


def get_upcoming_appointments_for_business(
    business: Business,
    limit: int = 20,
) -> QuerySet[Appointment]:
    """نوبت‌های آینده‌ی یه کسب‌وکار."""
    return (
        Appointment.objects.for_business(business)
        .upcoming()
        .with_relations()
        .order_by("start_at")[:limit]
    )


def get_overlapping_appointments(
    business: Business,
    start_at: datetime,
    end_at: datetime,
    station: Station | None = None,
) -> QuerySet[Appointment]:
    """
    نوبت‌های متداخل با یه بازه.

    برای چک availability استفاده میشه.
    """
    qs = Appointment.objects.for_business(business).overlapping(
        start_at, end_at
    )

    if station:
        qs = qs.filter(station=station)

    return qs


# ═══════════════════════════════════════════════════════════════
#  آمار
# ═══════════════════════════════════════════════════════════════


def get_business_stats(business: Business) -> dict:
    """
    آمار خلاصه‌ی یه کسب‌وکار.

    Returns:
        dict با کلیدها:
        - today_count
        - week_count
        - pending_count
        - confirmed_count
        - cancelled_count
        - waiting_count
        - blocked_count
    """
    today = timezone.localdate()
    week_ago = today - timezone.timedelta(days=7)

    appts = Appointment.objects.for_business(business)

    return {
        "today_count": appts.for_date(today).exclude(
            status=AppointmentStatus.CANCELLED
        ).count(),
        "week_count": appts.filter(
            start_at__date__gte=week_ago,
            start_at__date__lte=today,
        ).exclude(status=AppointmentStatus.CANCELLED).count(),
        "pending_count": appts.filter(
            status=AppointmentStatus.PENDING
        ).count(),
        "confirmed_count": appts.filter(
            status=AppointmentStatus.CONFIRMED
        ).count(),
        "cancelled_count": appts.filter(
            status=AppointmentStatus.CANCELLED
        ).count(),
        "waiting_count": WaitingList.objects.for_business(business)
        .filter(status=WaitingStatus.WAITING)
        .count(),
        "blocked_count": BlockedCustomer.objects.for_business(
            business
        ).count(),
    }


def get_golden_hours(
    business: Business,
    days: int = 30,
    top_n: int = 5,
) -> list[tuple[int, int]]:
    """
    ساعات طلایی — ساعت‌هایی که بیشترین نوبت رو دارن.

    Args:
        business: کسب‌وکار
        days: چند روز اخیر
        top_n: تعداد ساعت‌های برتر

    Returns:
        لیست [(hour, count), ...] مرتب‌شده نزولی
    """
    since = timezone.now() - timezone.timedelta(days=days)

    results = (
        Appointment.objects.for_business(business)
        .filter(start_at__gte=since)
        .exclude(status=AppointmentStatus.CANCELLED)
        .extra(select={"hour": "EXTRACT(hour FROM start_at)"})
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("-count")[:top_n]
    )

    return [(int(r["hour"]), r["count"]) for r in results]


# ═══════════════════════════════════════════════════════════════
#  Blocked
# ═══════════════════════════════════════════════════════════════


def get_blocked_customers(business: Business) -> QuerySet[BlockedCustomer]:
    """لیست سیاه یه کسب‌وکار."""
    return BlockedCustomer.objects.for_business(business).order_by(
        "-created_at"
    )


# ═══════════════════════════════════════════════════════════════
#  Waiting List
# ═══════════════════════════════════════════════════════════════


def get_business_waiting_list(
    business: Business,
    *,
    include_past: bool = False,
) -> QuerySet[WaitingList]:
    """لیست انتظار یه کسب‌وکار."""
    today = timezone.localdate()

    qs = WaitingList.objects.for_business(business).select_related(
        "customer", "service"
    )

    if not include_past:
        qs = qs.filter(date__gte=today)

    return qs.order_by("date", "preferred_time", "created_at")


def get_customer_waiting_items(customer: User) -> QuerySet[WaitingList]:
    """آیتم‌های لیست انتظار یه مشتری."""
    return (
        WaitingList.objects.filter(customer=customer)
        .select_related("business", "service")
        .order_by("-created_at")
    )