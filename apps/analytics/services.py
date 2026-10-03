"""
سرویس‌های analytics.

منطق سطح بالا که selectors رو ترکیب می‌کنه.
"""

from apps.business.models import Business

from .constants import DEFAULT_ANALYTICS_DAYS
from .selectors import (
    get_customer_stats,
    get_dormant_customers,
    get_golden_hours,
    get_golden_weekdays,
    get_overall_stats,
    get_revenue_by_day,
    get_service_stats,
)


class AnalyticsService:
    """
    سرویس آمار و گزارش‌ها.

    استفاده:
        service = AnalyticsService(business)
        dashboard = service.get_dashboard_data(days=30)
    """

    def __init__(self, business: Business) -> None:
        self.business = business

    # ═══════════════════════════════════════════════════════════
    #  Dashboard
    # ═══════════════════════════════════════════════════════════

    def get_dashboard_data(
        self,
        days: int = DEFAULT_ANALYTICS_DAYS,
    ) -> dict:
        """
        همه‌ی داده‌ی داشبورد آمار در یه کوئری.

        Returns:
            dict با همه‌ی بخش‌ها.
        """
        return {
            "overall": get_overall_stats(self.business, days),
            "golden_hours": get_golden_hours(self.business, days),
            "golden_weekdays": get_golden_weekdays(self.business, days),
            "service_stats": get_service_stats(self.business, days),
            "revenue_by_day": get_revenue_by_day(self.business, days),
            "top_customers": get_customer_stats(self.business, days),
            "days": days,
        }

    def get_dormant_customers_count(self, days: int = 90) -> int:
        """تعداد مشتریان خواب‌رفته."""
        return get_dormant_customers(self.business, days).count()