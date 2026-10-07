"""
Admin configuration برای support.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .constants import TicketStatus
from .models import Ticket, TicketAttachment, TicketMessage


# ═══════════════════════════════════════════════════════════════
#  Inlines
# ═══════════════════════════════════════════════════════════════


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1
    fields = ("user", "message", "is_staff_reply", "is_read")
    readonly_fields = ("created_at",)
    ordering = ("created_at",)


# ═══════════════════════════════════════════════════════════════
#  Ticket
# ═══════════════════════════════════════════════════════════════


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "user_link",
        "category_badge",
        "priority_badge",
        "status_badge",
        "messages_count",
        "created_at",
    )
    list_filter = ("status", "category", "priority", "created_at")
    search_fields = ("subject", "user__phone", "messages__message")
    readonly_fields = (
        "created_at",
        "updated_at",
        "closed_at",
        "last_reply_at",
    )
    date_hierarchy = "created_at"
    list_per_page = 30
    list_select_related = ("user", "assigned_to")
    inlines = [TicketMessageInline]
    actions = ["mark_in_progress", "mark_answered", "mark_closed"]

    fieldsets = (
        (
            _("اطلاعات تیکت"),
            {
                "fields": (
                    "user",
                    "subject",
                    "category",
                    "priority",
                    "status",
                )
            },
        ),
        (
            _("بررسی"),
            {"fields": ("assigned_to", "closed_at", "last_reply_at")},
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("کاربر"))
    def user_link(self, obj: Ticket) -> str:
        url = f"/admin/accounts/user/{obj.user.pk}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.user.phone)

    @admin.display(description=_("دسته"))
    def category_badge(self, obj: Ticket) -> str:
        return obj.get_category_display()

    @admin.display(description=_("اولویت"))
    def priority_badge(self, obj: Ticket) -> str:
        colors = {
            "low": "#6B7280",
            "normal": "#3B82F6",
            "high": "#EAB308",
            "urgent": "#EF4444",
        }
        color = colors.get(obj.priority, "#666")
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            obj.get_priority_display(),
        )

    @admin.display(description=_("وضعیت"))
    def status_badge(self, obj: Ticket) -> str:
        colors = {
            TicketStatus.OPEN: ("#3B82F6", "🔓 باز"),
            TicketStatus.IN_PROGRESS: ("#EAB308", "⏳ در بررسی"),
            TicketStatus.ANSWERED: ("#22C55E", "✅ پاسخ داده"),
            TicketStatus.CLOSED: ("#6B7280", "🔒 بسته"),
        }
        color, label = colors.get(obj.status, ("#666", obj.status))
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )

    @admin.display(description=_("تعداد پیام"))
    def messages_count(self, obj: Ticket) -> int:
        return obj.messages.count()

    @admin.action(description=_("⏳ در حال بررسی"))
    def mark_in_progress(self, request, queryset):
        count = queryset.update(status=TicketStatus.IN_PROGRESS)
        self.message_user(request, f"✅ {count} تیکت به «در بررسی» تغییر یافت.")

    @admin.action(description=_("✅ پاسخ داده شده"))
    def mark_answered(self, request, queryset):
        count = queryset.update(status=TicketStatus.ANSWERED)
        self.message_user(request, f"✅ {count} تیکت به «پاسخ داده» تغییر یافت.")

    @admin.action(description=_("🔒 بسته شده"))
    def mark_closed(self, request, queryset):
        count = queryset.update(
            status=TicketStatus.CLOSED,
            closed_at=timezone.now(),
        )
        self.message_user(request, f"✅ {count} تیکت بسته شد.")


# ═══════════════════════════════════════════════════════════════
#  TicketMessage
# ═══════════════════════════════════════════════════════════════


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ticket_link",
        "user",
        "is_staff_reply",
        "is_read",
        "created_at",
    )
    list_filter = ("is_staff_reply", "is_read", "created_at")
    search_fields = ("message", "user__phone", "ticket__subject")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("ticket", "user")
    list_per_page = 50

    @admin.display(description=_("تیکت"))
    def ticket_link(self, obj: TicketMessage) -> str:
        url = f"/admin/support/ticket/{obj.ticket.pk}/change/"
        return format_html('<a href="{}">#{}</a>', url, obj.ticket.pk)


# ═══════════════════════════════════════════════════════════════
#  TicketAttachment
# ═══════════════════════════════════════════════════════════════


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ticket_message",
        "original_name",
        "size_display",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("original_name", "ticket_message__message")
    readonly_fields = ("created_at", "updated_at", "file_size")
    list_select_related = ("ticket_message",)

    @admin.display(description=_("حجم"))
    def size_display(self, obj: TicketAttachment) -> str:
        return obj.size_display
from .models import PasswordResetRequest
@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display=("phone","full_name","status","user","created_at","handled_at")
    list_filter=("status",)
    search_fields=("phone","full_name","note")
