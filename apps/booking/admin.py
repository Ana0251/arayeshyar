"""
Admin configuration برای booking.

─── پاک‌سازی: ───
- BlockedCustomer → حذف شد (از پنل کسب‌وکار مدیریت میشه)
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .constants import AppointmentStatus, WaitingStatus
from .models import Appointment, WaitingList


# ═══════════════════════════════════════════════════════════════
#  Appointment
# ═══════════════════════════════════════════════════════════════


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin برای Appointment."""

    list_display = (
        "id",
        "business",
        "customer_display",
        "start_at",
        "service_name_snapshot",
        "status_badge",
        "station",
    )
    list_filter = (
        "status",
        "business",
        "station",
        "start_at",
    )
    search_fields = (
        "customer__phone",
        "customer__customer_profile__full_name",
        "business__name",
        "service_name_snapshot",
    )
    date_hierarchy = "start_at"
    readonly_fields = (
        "created_at",
        "updated_at",
        "confirmed_at",
        "cancelled_at",
    )
    autocomplete_fields = ("business", "customer", "service", "station")
    list_per_page = 50
    list_select_related = ("business", "customer", "service", "station")

    fieldsets = (
        (
            _("روابط"),
            {
                "fields": (
                    "business",
                    "customer",
                    "service",
                    "station",
                    "staff",
                )
            },
        ),
        (
            _("Snapshot خدمت"),
            {
                "fields": (
                    "service_name_snapshot",
                    "service_price_snapshot",
                    "service_duration_snapshot",
                )
            },
        ),
        (
            _("زمان"),
            {"fields": ("start_at", "end_at")},
        ),
        (
            _("وضعیت"),
            {
                "fields": (
                    "status",
                    "confirmed_at",
                    "cancelled_at",
                    "cancelled_by",
                    "cancellation_reason",
                )
            },
        ),
        (
            _("یادداشت‌ها"),
            {
                "fields": ("customer_note", "owner_note", "created_by"),
                "classes": ("collapse",),
            },
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("مشتری"))
    def customer_display(self, obj: Appointment) -> str:
        return obj.customer.display_name

    @admin.display(description=_("وضعیت"))
    def status_badge(self, obj: Appointment) -> str:
        colors = {
            AppointmentStatus.PENDING: ("#EAB308", "⏳ در انتظار"),
            AppointmentStatus.CONFIRMED: ("#22C55E", "✅ تأیید شده"),
            AppointmentStatus.CANCELLED: ("#EF4444", "❌ لغو شده"),
            AppointmentStatus.COMPLETED: ("#3B82F6", "✓ انجام شده"),
            AppointmentStatus.NO_SHOW: ("#6B7280", "⊘ عدم حضور"),
        }
        color, label = colors.get(obj.status, ("#666", obj.status))
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )


# ═══════════════════════════════════════════════════════════════
#  WaitingList
# ═══════════════════════════════════════════════════════════════


@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    """Admin برای WaitingList."""

    list_display = (
        "business",
        "customer_display",
        "date",
        "preferred_time",
        "service_name_snapshot",
        "status_badge",
        "created_at",
    )
    list_filter = ("status", "business", "date")
    search_fields = (
        "customer__phone",
        "customer__customer_profile__full_name",
        "business__name",
    )
    date_hierarchy = "date"
    autocomplete_fields = ("business", "customer", "service")
    list_per_page = 50
    list_select_related = ("business", "customer", "service")

    @admin.display(description=_("مشتری"))
    def customer_display(self, obj: WaitingList) -> str:
        return obj.customer.display_name

    @admin.display(description=_("وضعیت"))
    def status_badge(self, obj: WaitingList) -> str:
        colors = {
            WaitingStatus.WAITING: ("#EAB308", "⏳ در انتظار"),
            WaitingStatus.NOTIFIED: ("#22C55E", "✓ اطلاع داده شده"),
            WaitingStatus.EXPIRED: ("#6B7280", "⊘ منقضی"),
            WaitingStatus.CANCELLED: ("#EF4444", "❌ لغو شده"),
            WaitingStatus.CONVERTED: ("#3B82F6", "→ تبدیل شد"),
        }
        color, label = colors.get(obj.status, ("#666", obj.status))
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )


# ═══════════════════════════════════════════════════════════════
#  BlockedCustomer — حذف شد
# ═══════════════════════════════════════════════════════════════
# @admin.register(BlockedCustomer)  ← حذف شد
# class BlockedCustomerAdmin(admin.ModelAdmin):
#     ...