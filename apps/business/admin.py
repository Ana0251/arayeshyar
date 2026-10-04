"""
Admin configuration برای business.

شامل admin برای ۱۱ مدل با inline و actions.

─── پاک‌سازی: ───
- BusinessOwnerProfile → توی accounts/admin.py هست
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .constants import (
    ChangeRequestStatus,
    PaymentStatus,
)
from .models import (
    ActivityType,
    Break,
    Business,
    DayOff,
    Payment,
    Plan,
    ProfileChangeRequest,
    Service,
    SpecialWorkingHours,
    Staff,
    Station,
    TargetAudience,
    WorkingHours,
)


# ═══════════════════════════════════════════════════════════════
#  Inlines
# ═══════════════════════════════════════════════════════════════


class StationInline(admin.TabularInline):
    """Inline ایستگاه‌ها توی Business."""

    model = Station
    extra = 0
    fields = ("name", "order", "is_active")
    ordering = ("order",)
    show_change_link = True


class StaffInline(admin.TabularInline):
    """Inline کارمندها توی Business."""

    model = Staff
    extra = 0
    fields = ("name", "phone", "is_owner", "is_active", "order")
    ordering = ("-is_owner", "order")
    show_change_link = True


class ServiceInline(admin.TabularInline):
    """Inline خدمات توی Business."""

    model = Service
    extra = 0
    fields = ("name", "station", "duration", "price", "is_active")
    ordering = ("order", "name")
    show_change_link = True
    autocomplete_fields = ("station",)


# ═══════════════════════════════════════════════════════════════
#  TargetAudience + ActivityType
# ═══════════════════════════════════════════════════════════════


@admin.register(TargetAudience)
class TargetAudienceAdmin(admin.ModelAdmin):
    list_display = ("icon", "name", "slug", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("order",)


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ("icon", "name", "slug", "is_salon", "order", "is_active")
    list_editable = ("is_salon", "order", "is_active")
    list_filter = ("is_salon", "is_active")
    search_fields = ("name", "slug")
    ordering = ("is_salon", "order")

# ═══════════════════════════════════════════════════════════════
#  Plan
# ═══════════════════════════════════════════════════════════════


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin برای Plan."""

    list_display = (
        "icon",
        "name",
        "slug",
        "price_display",
        "duration_days",
        "features_count",
        "order",
        "is_active",
        "is_paid",
        "has_pro_features",
    )
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "is_paid", "has_pro_features")
    search_fields = ("name", "slug", "description")
    ordering = ("order", "price")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            _("اطلاعات پایه"),
            {
                "fields": (
                    "slug",
                    "name",
                    "icon",
                    "description",
                    "order",
                )
            },
        ),
        (
            _("قیمت و مدت"),
            {
                "fields": (
                    "price",
                    "duration_days",
                )
            },
        ),
        (
            _("ویژگی‌ها"),
            {
                "fields": ("features",),
                "description": _(
                    "لیست ویژگی‌ها رو به صورت JSON بنویس. مثال: "
                    '["نوبت‌دهی آنلاین", "QR Code"]'
                ),
            },
        ),
        (
            _("وضعیت"),
            {
                "fields": (
                    "is_active",
                    "is_paid",
                    "has_pro_features",
                )
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

    @admin.display(description=_("قیمت"))
    def price_display(self, obj: Plan) -> str:
        if not obj.is_paid or obj.price == 0:
            return "رایگان"
        return f"{obj.price:,} تومان"

    @admin.display(description=_("تعداد ویژگی"))
    def features_count(self, obj: Plan) -> int:
        return obj.features_count
    
# ═══════════════════════════════════════════════════════════════
#  Business
# ═══════════════════════════════════════════════════════════════


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """Admin برای Business."""

    list_display = (
        "name",
        "owner_link",
        "activity_type",
        "region",
        "plan_badge",
        "status_badge",
        "pending_changes_badge",
        "created_at",
    )
    list_filter = (
        "is_active",
        "is_rejected",
        "is_salon",
        "plan",
        "activity_type",
        "target_audience",
        "created_at",
    )
    search_fields = (
        "name",
        "slug",
        "owner__phone",
        "region",
        "owner_name",
    )
    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
        "plan_days_left_display",
    )
    date_hierarchy = "created_at"
    inlines = [StaffInline, StationInline, ServiceInline]
    list_per_page = 30
    list_select_related = (
        "owner",
        "activity_type",
        "target_audience",
    )
    actions = ["approve_businesses", "reject_businesses"]

    fieldsets = (
        (_("مالکیت"), {"fields": ("owner",)}),
        (
            _("نوع کسب‌وکار"),
            {"fields": ("target_audience", "activity_type", "is_salon")},
        ),
        (
            _("اطلاعات پایه"),
            {
                "fields": (
                    "name",
                    "slug",
                    "owner_name",
                    "landline",
                    "region",
                    "address",
                    "bio",
                )
            },
        ),
        (
            _("تصاویر"),
            {
                "fields": ("avatar", "business_license", "entrance_photo"),
                "classes": ("collapse",),
            },
        ),
        (
            _("وضعیت تأیید"),
            {"fields": ("is_active", "is_rejected", "rejection_reason")},
        ),
        (
            _("پلن"),
            {
                "fields": (
                    "plan",
                    "plan_expires_at",
                    "plan_days_left_display",
                )
            },
        ),
        (_("تنظیمات"), {"fields": ("auto_confirm",)}),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ═══════════════════════════════════════════════════════════
    #  Columns
    # ═══════════════════════════════════════════════════════════

    @admin.display(description=_("صاحب"))
    def owner_link(self, obj: Business) -> str:
        """لینک به کاربر صاحب."""
        url = f"/admin/accounts/user/{obj.owner.pk}/change/"
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.owner.phone,
        )

    @admin.display(description=_("پلن"))
    def plan_badge(self, obj: Business) -> str:
        """پلن با رنگ."""
        colors = {
            Plan.TRIAL: ("#6B7280", "🎁 تست"),
            Plan.BASIC: ("#3B82F6", "⭐ پایه"),
            Plan.PRO: ("#B08D57", "💎 ویژه"),
        }
        color, label = colors.get(obj.plan, ("#666", obj.plan))
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )

    @admin.display(description=_("وضعیت"))
    def status_badge(self, obj: Business) -> str:
        """وضعیت با رنگ."""
        if obj.is_rejected:
            color, label = "#EF4444", "❌ رد شده"
        elif obj.is_active:
            color, label = "#22C55E", "✅ فعال"
        else:
            color, label = "#EAB308", "⏳ در انتظار"
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )

    @admin.display(description=_("درخواست‌های معلق"))
    def pending_changes_badge(self, obj: Business) -> str:
        """تعداد درخواست‌های معلق."""
        count = obj.pending_changes_count
        if count > 0:
            return format_html(
                '<span style="background:#EAB308; color:white; padding:3px 10px; '
                'border-radius:12px; font-weight:bold;">⏳ {}</span>',
                count,
            )
        return "—"

    @admin.display(description=_("روزهای باقی‌مانده"))
    def plan_days_left_display(self, obj: Business) -> str:
        """نمایش روزهای باقی‌مانده‌ی پلن."""
        if not obj.plan_expires_at:
            return "—"
        days = obj.plan_days_left
        if days is None:
            return "—"
        if days < 0:
            return format_html(
                '<span style="color:#EF4444; font-weight:bold;">'
                '{} روز گذشته</span>',
                abs(days),
            )
        if days <= 7:
            return format_html(
                '<span style="color:#EAB308; font-weight:bold;">'
                '{} روز مونده</span>',
                days,
            )
        return format_html(
            '<span style="color:#22C55E; font-weight:bold;">'
            '{} روز مونده</span>',
            days,
        )

    # ═══════════════════════════════════════════════════════════
    #  Actions
    # ═══════════════════════════════════════════════════════════

    @admin.action(description=_("✅ تأیید انتخاب‌شده‌ها"))
    def approve_businesses(self, request, queryset):
        count = queryset.update(
            is_active=True,
            is_rejected=False,
            rejection_reason="",
        )
        self.message_user(request, f"✅ {count} کسب‌وکار تأیید شد.")

    @admin.action(description=_("❌ رد انتخاب‌شده‌ها"))
    def reject_businesses(self, request, queryset):
        count = queryset.update(is_active=False, is_rejected=True)
        self.message_user(request, f"❌ {count} کسب‌وکار رد شد.")


# ═══════════════════════════════════════════════════════════════
#  Staff
# ═══════════════════════════════════════════════════════════════


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "business",
        "is_owner_badge",
        "phone",
        "is_active",
        "order",
    )
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "is_owner", "business")
    search_fields = ("name", "phone", "business__name")
    ordering = ("business", "-is_owner", "order")
    autocomplete_fields = ("business",)
    list_select_related = ("business",)

    fieldsets = (
        (
            _("اطلاعات پایه"),
            {"fields": ("business", "name", "phone", "avatar", "bio")},
        ),
        (
            _("وضعیت"),
            {"fields": ("is_owner", "is_active", "order")},
        ),
    )

    @admin.display(description=_("صاحب"), boolean=True)
    def is_owner_badge(self, obj):
        return obj.is_owner


# ═══════════════════════════════════════════════════════════════
#  Service
# ═══════════════════════════════════════════════════════════════


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "business",
        "station",
        "duration",
        "price",
        "staff_count_display",
        "is_active",
        "order",
    )
    list_editable = ("duration", "price", "is_active", "order")
    list_filter = ("is_active", "business", "station")
    search_fields = ("name", "business__name", "station__name")
    ordering = ("business", "order")
    autocomplete_fields = ("business", "station")
    filter_horizontal = ("staff_members",)
    list_select_related = ("business", "station")

    fieldsets = (
        (
            _("اطلاعات خدمت"),
            {"fields": ("business", "station", "name", "duration", "price")},
        ),
        (
            _("مسئول‌ها"),
            {
                "fields": ("staff_members",),
                "description": _("کارمندهایی که این خدمت رو انجام می‌دن"),
            },
        ),
        (
            _("وضعیت"),
            {"fields": ("is_active", "order")},
        ),
    )

    @admin.display(description=_("تعداد مسئول"))
    def staff_count_display(self, obj):
        return obj.staff_count


# ═══════════════════════════════════════════════════════════════
#  Station
# ═══════════════════════════════════════════════════════════════


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "business",
        "services_count_display",
        "order",
        "is_active",
    )
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "business")
    search_fields = ("name", "business__name")
    ordering = ("business", "order")
    autocomplete_fields = ("business",)
    filter_horizontal = ("staff_members",)
    list_select_related = ("business",)

    fieldsets = (
        (
            _("اطلاعات ایستگاه"),
            {"fields": ("business", "name", "order", "is_active")},
        ),
        (
            _("کارمندها"),
            {
                "fields": ("staff_members",),
                "description": _(
                    "کارمندهایی که توی این ایستگاه کار می‌کنن (اختیاری)"
                ),
            },
        ),
    )

    @admin.display(description=_("تعداد خدمات"))
    def services_count_display(self, obj):
        return obj.services_count


# ═══════════════════════════════════════════════════════════════
#  WorkingHours / DayOff / SpecialWorkingHours / Break
# ═══════════════════════════════════════════════════════════════


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = (
        "business",
        "station",
        "get_weekday_display",
        "start_time",
        "end_time",
        "is_active",
    )
    list_editable = ("is_active",)
    list_filter = ("weekday", "is_active", "business", "station")
    autocomplete_fields = ("business", "station")
    list_select_related = ("business", "station")


@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ("business", "station", "date", "reason")
    list_filter = ("business", "station", "date")
    search_fields = ("business__name", "reason")
    date_hierarchy = "date"
    autocomplete_fields = ("business", "station")
    list_select_related = ("business", "station")


@admin.register(SpecialWorkingHours)
class SpecialWorkingHoursAdmin(admin.ModelAdmin):
    list_display = (
        "business",
        "station",
        "date",
        "start_time",
        "end_time",
        "note",
    )
    list_filter = ("business", "station", "date")
    search_fields = ("business__name", "note")
    date_hierarchy = "date"
    autocomplete_fields = ("business", "station")
    list_select_related = ("business", "station")


@admin.register(Break)
class BreakAdmin(admin.ModelAdmin):
    list_display = (
        "business",
        "station",
        "start_time",
        "end_time",
        "label",
        "is_active",
    )
    list_editable = ("is_active",)
    list_filter = ("is_active", "business", "station")
    search_fields = ("business__name", "label")
    autocomplete_fields = ("business", "station")
    list_select_related = ("business", "station")


# ═══════════════════════════════════════════════════════════════
#  ProfileChangeRequest
# ═══════════════════════════════════════════════════════════════


@admin.register(ProfileChangeRequest)
class ProfileChangeRequestAdmin(admin.ModelAdmin):
    """Admin برای ProfileChangeRequest."""

    list_display = (
        "business",
        "field_name_badge",
        "status_badge",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status", "field_name", "created_at")
    search_fields = ("business__name", "business__owner__phone")
    date_hierarchy = "created_at"
    readonly_fields = (
        "business",
        "field_name",
        "old_value_display",
        "new_value_display",
        "created_at",
        "reviewed_at",
        "reviewed_by",
    )
    list_per_page = 30
    list_select_related = ("business", "reviewed_by")
    actions = ["approve_changes", "reject_changes"]

    fieldsets = (
        (
            _("اطلاعات درخواست"),
            {
                "fields": (
                    "business",
                    "field_name",
                    "status",
                    "created_at",
                    "reviewed_at",
                    "reviewed_by",
                )
            },
        ),
        (_("مقدار قبلی"), {"fields": ("old_value_display",)}),
        (_("مقدار جدید"), {"fields": ("new_value_display",)}),
        (_("دلیل رد"), {"fields": ("rejection_reason",)}),
    )

    # ═══════════════════════════════════════════════════════════
    #  Columns
    # ═══════════════════════════════════════════════════════════

    @admin.display(description=_("فیلد"))
    def field_name_badge(self, obj: ProfileChangeRequest) -> str:
        return obj.get_field_name_display()

    @admin.display(description=_("وضعیت"))
    def status_badge(self, obj: ProfileChangeRequest) -> str:
        colors = {
            ChangeRequestStatus.PENDING: ("#EAB308", "⏳ در انتظار"),
            ChangeRequestStatus.APPROVED: ("#22C55E", "✅ تأیید شده"),
            ChangeRequestStatus.REJECTED: ("#EF4444", "❌ رد شده"),
        }
        color, label = colors.get(obj.status, ("#666", obj.status))
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )

    @admin.display(description=_("مقدار قبلی"))
    def old_value_display(self, obj: ProfileChangeRequest) -> str:
        """نمایش مقدار قبلی (متن یا عکس)."""
        if obj.is_file_field:
            if obj.old_value_text:
                return format_html(
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width:200px; max-height:200px; '
                    'border-radius:8px; border:2px solid #ddd;"></a>',
                    obj.old_value_text,
                    obj.old_value_text,
                )
            return "— نداشت"
        return obj.old_value_text or "— خالی"

    @admin.display(description=_("مقدار جدید"))
    def new_value_display(self, obj: ProfileChangeRequest) -> str:
        """نمایش مقدار جدید (متن یا عکس)."""
        if obj.is_file_field:
            if obj.new_value_file:
                return format_html(
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width:200px; max-height:200px; '
                    'border-radius:8px; border:2px solid #22C55E;"></a>',
                    obj.new_value_file.url,
                    obj.new_value_file.url,
                )
            return "🗑️ حذف"
        return obj.new_value_text or "— خالی"

    # ═══════════════════════════════════════════════════════════
    #  Actions
    # ═══════════════════════════════════════════════════════════

    @admin.action(description=_("✅ تأیید و اعمال انتخاب‌شده‌ها"))
    def approve_changes(self, request, queryset):
        count = 0
        for req in queryset.filter(status=ChangeRequestStatus.PENDING):
            req.approve(reviewed_by=request.user)
            count += 1
        self.message_user(request, f"✅ {count} درخواست تأیید و اعمال شد.")

    @admin.action(description=_("❌ رد انتخاب‌شده‌ها"))
    def reject_changes(self, request, queryset):
        count = 0
        for req in queryset.filter(status=ChangeRequestStatus.PENDING):
            req.reject(
                reason="به‌صورت گروهی رد شد",
                reviewed_by=request.user,
            )
            count += 1
        self.message_user(request, f"❌ {count} درخواست رد شد.")


# ═══════════════════════════════════════════════════════════════
#  Payment
# ═══════════════════════════════════════════════════════════════


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin برای Payment."""

    list_display = (
        "business",
        "plan_badge",
        "amount_display",
        "status_badge",
        "method",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status", "plan", "method", "created_at")
    search_fields = (
        "business__name",
        "tracking_code",
        "business__owner__phone",
    )
    date_hierarchy = "created_at"
    readonly_fields = (
        "business",
        "plan",
        "amount",
        "method",
        "created_at",
        "updated_at",
        "reviewed_at",
        "reviewed_by",
        "receipt_preview",
    )
    list_per_page = 30
    list_select_related = ("business", "reviewed_by")
    actions = ["approve_payments", "reject_payments"]

    fieldsets = (
        (
            _("اطلاعات پرداخت"),
            {
                "fields": (
                    "business",
                    "plan",
                    "amount",
                    "method",
                    "status",
                    "tracking_code",
                )
            },
        ),
        (_("رسید"), {"fields": ("receipt_preview",)}),
        (_("یادداشت‌ها"), {"fields": ("customer_note", "admin_note")}),
        (_("بررسی"), {"fields": ("reviewed_at", "reviewed_by")}),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ═══════════════════════════════════════════════════════════
    #  Columns
    # ═══════════════════════════════════════════════════════════

    @admin.display(description=_("پلن"))
    def plan_badge(self, obj: Payment) -> str:
        if not obj.plan:
            return "—"
        return f"{obj.plan.icon} {obj.plan.name}"

    @admin.display(description=_("مبلغ"))
    def amount_display(self, obj: Payment) -> str:
        return f"{obj.amount:,} تومان"

    @admin.display(description=_("وضعیت"))
    def status_badge(self, obj: Payment) -> str:
        colors = {
            PaymentStatus.PENDING: ("#EAB308", "⏳ در انتظار"),
            PaymentStatus.APPROVED: ("#22C55E", "✅ تأیید شده"),
            PaymentStatus.REJECTED: ("#EF4444", "❌ رد شده"),
        }
        color, label = colors.get(obj.status, ("#666", obj.status))
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )

    @admin.display(description=_("پیش‌نمایش رسید"))
    def receipt_preview(self, obj: Payment) -> str:
        """نمایش رسید به‌صورت عکس."""
        if obj.receipt:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width:400px; max-height:400px; '
                'border-radius:8px; border:2px solid #ddd;"></a>',
                obj.receipt.url,
                obj.receipt.url,
            )
        return "—"

    # ═══════════════════════════════════════════════════════════
    #  Actions
    # ═══════════════════════════════════════════════════════════

    @admin.action(description=_("✅ تأیید و فعال‌سازی پلن"))
    def approve_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status=PaymentStatus.PENDING):
            payment.approve(
                reviewed_by=request.user,
                note="تأیید گروهی",
            )
            count += 1
        self.message_user(
            request,
            f"✅ {count} پرداخت تأیید و پلن فعال شد.",
        )

    @admin.action(description=_("❌ رد پرداخت‌ها"))
    def reject_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status=PaymentStatus.PENDING):
            payment.reject(
                reason="به‌صورت گروهی رد شد",
                reviewed_by=request.user,
            )
            count += 1
        self.message_user(request, f"❌ {count} پرداخت رد شد.")