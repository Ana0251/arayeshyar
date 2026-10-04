"""
Selectors — کوئری‌های تحلیلی.

همه‌ی query های پیچیده اینجا متمرکزن.
"""

from datetime import date, timedelta
from typing import TYPE_CHECKING

from django.db import connection
from django.db.models import Avg, Count, Max, Q, QuerySet, Sum
from django.utils import timezone

from apps.accounts.models import User
from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment
from apps.business.constants import Weekday
from apps.business.models import Business, Service


from .constants import (
    DEFAULT_ANALYTICS_DAYS,
    GOLDEN_HOURS_TOP_N,
    GOLDEN_WEEKDAYS_TOP_N,
    DORMANT_CUSTOMER_DAYS,
)

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _date_range(days: int) -> tuple[date, date]:
    """محاسبه‌ی بازه‌ی تاریخ."""
    today = timezone.localdate()
    start = today - timedelta(days=days)
    return start, today


def _base_appointments_query(
    business: Business,
    days: int,
) -> QuerySet[Appointment]:
    """
    کوئری پایه برای همه‌ی تحلیل‌ها.

    فقط نوبت‌های:
    - توی بازه‌ی مشخص
    - غیر لغو‌شده
    - انجام‌شده یا تأییدشده
    """
    start_date, end_date = _date_range(days)

    return Appointment.objects.for_business(business).filter(
        start_at__date__gte=start_date,
        start_at__date__lte=end_date,
    ).exclude(
        status=AppointmentStatus.CANCELLED,
    )


# ═══════════════════════════════════════════════════════════════
#  آمار کلی
# ═══════════════════════════════════════════════════════════════


def get_overall_stats(
    business: Business,
    days: int = DEFAULT_ANALYTICS_DAYS,
) -> dict:
    """
    آمار کلی کسب‌وکار.

    Returns:
        dict با کلیدها:
        - total_appointments
        - completed_count
        - cancelled_count
        - no_show_count
        - pending_count
        - unique_customers
        - total_revenue (تخمینی)
        - avg_revenue_per_appointment
        - no_show_rate
        - completion_rate
    """
    qs = _base_appointments_query(business, days)

    # ─── شمارش‌ها ───
    counts = qs.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=AppointmentStatus.COMPLETED)),
        confirmed=Count("id", filter=Q(status=AppointmentStatus.CONFIRMED)),
        pending=Count("id", filter=Q(status=AppointmentStatus.PENDING)),
        no_show=Count("id", filter=Q(status=AppointmentStatus.NO_SHOW)),
        unique_customers=Count("customer", distinct=True),
    )

    # ─── نوبت‌های لغو‌شده (جدا، چون از base حذف شدن) ───
    start_date, end_date = _date_range(days)
    cancelled = (
        Appointment.objects.for_business(business)
        .filter(
            start_at__date__gte=start_date,
            start_at__date__lte=end_date,
            status=AppointmentStatus.CANCELLED,
        )
        .count()
    )

    # ─── درآمد تخمینی ───
    revenue = (
        qs.filter(
            status__in=[
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.COMPLETED,
            ]
        )
        .aggregate(total=Sum("service_price_snapshot"))
    )["total"] or 0

    total = counts["total"] + cancelled
    completed = counts["completed"]

    # ─── نرخ‌ها ───
    no_show_rate = (counts["no_show"] / total * 100) if total else 0
    completion_rate = (completed / total * 100) if total else 0
    avg_revenue = (revenue / completed) if completed else 0

    return {
        "total_appointments": total,
        "completed_count": completed,
        "confirmed_count": counts["confirmed"],
        "pending_count": counts["pending"],
        "cancelled_count": cancelled,
        "no_show_count": counts["no_show"],
        "unique_customers": counts["unique_customers"],
        "total_revenue": revenue,
        "avg_revenue_per_appointment": int(avg_revenue),
        "no_show_rate": round(no_show_rate, 1),
        "completion_rate": round(completion_rate, 1),
    }


# ═══════════════════════════════════════════════════════════════
#  ساعات طلایی
# ═══════════════════════════════════════════════════════════════


def get_golden_hours(
    business: Business,
    days: int = DEFAULT_ANALYTICS_DAYS,
    top_n: int = GOLDEN_HOURS_TOP_N,
) -> list[dict]:
    """
    ساعات طلایی — پرترافیک‌ترین ساعت‌ها.

    ─── نکته: ───
    به جای EXTRACT (که روی SQLite کار نمی‌کنه)، از Python استفاده می‌کنیم.
    برای حجم‌های بزرگ، بهتره از annotation database-specific استفاده بشه.

    Returns:
        لیست dict با کلیدها:
        - hour (0-23)
        - label ("09:00")
        - count
        - percentage
        - is_golden
    """
    qs = _base_appointments_query(business, days)

    # ─── شمارش به تفکیک ساعت (در Python) ───
    counts_by_hour: dict[int, int] = {}

    for appt in qs.only("start_at"):
        # ─── تبدیل به Tehran بعد ساعت رو بگیر ───
        local_dt = timezone.localtime(appt.start_at)
        hour = local_dt.hour
        counts_by_hour[hour] = counts_by_hour.get(hour, 0) + 1

    if not counts_by_hour:
        return []

    max_count = max(counts_by_hour.values()) if counts_by_hour else 1

    # ─── مرتب‌سازی برترها ───
    top_hours = sorted(
        counts_by_hour.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:top_n]
    top_hour_set = {h for h, _ in top_hours}

    # ─── ساخت نتیجه ───
    result = []
    for hour in range(24):
        count = counts_by_hour.get(hour, 0)
        if count == 0:
            continue

        result.append({
            "hour": hour,
            "label": f"{hour:02d}:00",
            "count": count,
            "percentage": round(count / max_count * 100, 1),
            "is_golden": hour in top_hour_set,
        })

    return result


def get_customer_stats(
    business: Business,
    days: int = DEFAULT_ANALYTICS_DAYS,
    top_n: int = 10,
) -> list[dict]:
    """
    آمار مشتریان برتر (بیشترین نوبت).

    Returns:
        لیست dict با کلیدها:
        - customer
        - appointments_count
        - total_spent
        - last_visit_at
    """
    qs = _base_appointments_query(business, days)

    # ─── آمار تجمیعی ───
    results = list(
        qs.filter(
            status__in=[
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.COMPLETED,
            ]
        )
        .values("customer")
        .annotate(
            appointments_count=Count("id"),
            total_spent=Sum("service_price_snapshot"),
        )
        .order_by("-appointments_count")[:top_n]
    )

    if not results:
        return []

    customer_ids = [r["customer"] for r in results]

    # ─── آخرین بازدید هر مشتری (جدا) ───
    last_visits = (
        Appointment.objects.for_business(business)
        .filter(customer_id__in=customer_ids)
        .exclude(status=AppointmentStatus.CANCELLED)
        .values("customer")
        .annotate(last_visit_at=Max("start_at"))
    )
    last_visit_map = {r["customer"]: r["last_visit_at"] for r in last_visits}

    # ─── اطلاعات مشتری ───
    customers_map = {
        u.id: u
        for u in User.objects.filter(id__in=customer_ids).select_related(
            "customer_profile"
        )
    }

    output = []
    for row in results:
        customer = customers_map.get(row["customer"])
        if not customer:
            continue

        output.append({
            "customer": customer,
            "appointments_count": row["appointments_count"],
            "total_spent": row["total_spent"] or 0,
            "last_visit_at": last_visit_map.get(row["customer"]),
        })

    return output


# ═══════════════════════════════════════════════════════════════
#  تحلیل خدمات
# ═══════════════════════════════════════════════════════════════


def get_service_stats(
    business: Business,
    days: int = DEFAULT_ANALYTICS_DAYS,
    top_n: int = 10,
) -> list[dict]:
    """
    آمار خدمات برتر.

    Returns:
        لیست dict با کلیدها:
        - service_name
        - count
        - revenue
        - avg_price
    """
    qs = _base_appointments_query(business, days).filter(
        status__in=[
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.COMPLETED,
        ]
    )

    results = (
        qs.values("service_name_snapshot")
        .annotate(
            count=Count("id"),
            revenue=Sum("service_price_snapshot"),
            avg_price=Avg("service_price_snapshot"),
        )
        .order_by("-count")[:top_n]
    )

    return [
        {
            "service_name": r["service_name_snapshot"],
            "count": r["count"],
            "revenue": r["revenue"] or 0,
            "avg_price": int(r["avg_price"] or 0),
        }
        for r in results
    ]


# ═══════════════════════════════════════════════════════════════
#  تحلیل درآمد
# ═══════════════════════════════════════════════════════════════


def get_revenue_by_day(
    business: Business,
    days: int = DEFAULT_ANALYTICS_DAYS,
) -> list[dict]:
    """
    درآمد روزانه.

    Returns:
        لیست dict با کلیدها:
        - date
        - revenue
        - count
    """
    qs = _base_appointments_query(business, days).filter(
        status__in=[
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.COMPLETED,
        ]
    )

    # ─── گروه‌بندی بر اساس تاریخ (میلادی) ───
    daily_data: dict[date, dict] = {}

    for appt in qs.only("start_at", "service_price_snapshot"):
        d = appt.start_at.date()
        if d not in daily_data:
            daily_data[d] = {"date": d, "revenue": 0, "count": 0}
        daily_data[d]["revenue"] += appt.service_price_snapshot
        daily_data[d]["count"] += 1

    return sorted(daily_data.values(), key=lambda x: x["date"])

def get_golden_weekdays(
    business: Business,
    days: int = DEFAULT_ANALYTICS_DAYS,
    top_n: int = GOLDEN_WEEKDAYS_TOP_N,
) -> list[dict]:
    """
    روزهای طلایی — پرترافیک‌ترین روزهای هفته.

    Returns:
        لیست dict با کلیدها:
        - weekday (0-6، شنبه=۰)
        - name ("شنبه")
        - count
        - percentage
        - is_golden
    """
    from apps.business.constants import Weekday

    qs = _base_appointments_query(business, days)

    # ─── شمارش به تفکیک روز هفته ───
    counts_by_weekday: dict[int, int] = {i: 0 for i in range(7)}

    for appt in qs.only("start_at"):
        # ─── تبدیل به Tehran ───
        local_dt = timezone.localtime(appt.start_at)
        python_weekday = local_dt.weekday()
        iranian_weekday = Weekday.from_python_weekday(python_weekday)
        counts_by_weekday[iranian_weekday] += 1

    if not any(counts_by_weekday.values()):
        return []

    max_count = max(counts_by_weekday.values())

    # ─── برترها ───
    top_weekdays = sorted(
        counts_by_weekday.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:top_n]
    top_weekday_set = {w for w, _ in top_weekdays}

    # ─── ساخت نتیجه ───
    result = []
    for weekday_value, name in Weekday.choices:
        count = counts_by_weekday.get(weekday_value, 0)
        result.append({
            "weekday": weekday_value,
            "name": name,
            "count": count,
            "percentage": round(count / max_count * 100, 1) if max_count else 0,
            "is_golden": weekday_value in top_weekday_set and count > 0,
        })

    return result