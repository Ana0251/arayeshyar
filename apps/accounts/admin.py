"""
Admin configuration برای accounts.

─── پاک‌سازی: ───
- OTPCode → حذف شد (غیرضروری برای ادمین)
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .constants import Role
from .models import BusinessOwnerProfile, CustomerProfile, User


# ═══════════════════════════════════════════════════════════════
#  User
# ═══════════════════════════════════════════════════════════════


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin برای User."""

    list_display = (
        "phone",
        "email",
        "display_name_short",
        "role_badge",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "phone")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "last_login_ip")
    list_per_page = 50
    date_hierarchy = "date_joined"

    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        (
            _("نقش و دسترسی"),
            {"fields": ("role", "is_active", "is_staff", "is_superuser")},
        ),
        (
            _("تاریخ‌ها"),
            {"fields": ("date_joined", "last_login", "last_login_ip")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "phone", "role", "password1", "password2"),
            },
        ),
    )

    @admin.display(description=_("نام نمایشی"))
    def display_name_short(self, obj: User) -> str:
        """نام کوتاه برای نمایش."""
        name = obj.display_name
        if len(name) > 30:
            return name[:30] + "..."
        return name

    @admin.display(description=_("نقش"))
    def role_badge(self, obj: User) -> str:
        """نقش با رنگ."""
        from django.utils.html import format_html

        colors = {
            Role.CUSTOMER: ("#3B82F6", "مشتری"),
            Role.BUSINESS_OWNER: ("#B08D57", "صاحب کسب‌وکار"),
            Role.ADMIN: ("#EF4444", "مدیر"),
        }
        color, label = colors.get(obj.role, ("#666", obj.role))
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            label,
        )


# ═══════════════════════════════════════════════════════════════
#  CustomerProfile
# ═══════════════════════════════════════════════════════════════


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """Admin برای CustomerProfile."""

    list_display = (
        "user",
        "full_name",
        "hide_ads_banner",
        "created_at",
    )
    list_filter = ("hide_ads_banner", "created_at")
    search_fields = ("user__email", "user__phone", "full_name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user",)
    list_per_page = 50
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("اطلاعات پایه"),
            {"fields": ("user", "full_name")},
        ),
        (
            _("تنظیمات"),
            {"fields": ("hide_ads_banner", "notes")},
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# ═══════════════════════════════════════════════════════════════
#  BusinessOwnerProfile
# ═══════════════════════════════════════════════════════════════


@admin.register(BusinessOwnerProfile)
class BusinessOwnerProfileAdmin(admin.ModelAdmin):
    """Admin برای BusinessOwnerProfile."""

    list_display = (
        "user",
        "business_name",
        "national_id",
        "created_at",
    )
    search_fields = (
        "user__email",
        "user__phone",
        "national_id",
        "user__business__name",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user",)
    list_per_page = 50
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("اطلاعات پایه"),
            {"fields": ("user", "national_id")},
        ),
        (
            _("تاریخ‌ها"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("کسب‌وکار"))
    def business_name(self, obj: BusinessOwnerProfile) -> str:
        """اسم کسب‌وکار (اگه وجود داره)."""
        business = getattr(obj.user, "business", None)
        if business:
            return business.name
        return "—"


