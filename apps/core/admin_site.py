"""
تنظیمات AdminSite برای آرایشیار.

─── هدف: ───
- مخفی‌کردن اپ‌های خالی
- مرتب‌سازی اپ‌ها به ترتیب منطقی

─── چرا Monkey Patch؟ ───
Django به‌طور پیش‌فرض `admin.site` رو global می‌کنه و همه‌ی
`@admin.register` ها روی همین ثبت میشن. برای اینکه بتونیم
`get_app_list` رو override کنیم بدون بازنویسی همه‌چیز، از
monkey patch استفاده می‌کنیم.
"""

import logging

from django.contrib import admin

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ترتیب اپ‌ها
# ═══════════════════════════════════════════════════════════════

VISIBLE_APPS_ORDER = [
    "accounts",       # کاربران
    "business",       # کسب‌وکارها
    "booking",        # نوبت‌دهی
]

HIDDEN_APPS = [
    "core",
    "customers",
    "notifications",
    "analytics",
    "auth",           # Group و Permission
]


# ═══════════════════════════════════════════════════════════════
#  Override get_app_list
# ═══════════════════════════════════════════════════════════════


def _custom_get_app_list(self, request, app_label=None):
    """
    لیست اپ‌ها رو با فیلتر و ترتیب سفارشی برمی‌گردونه.
    """
    app_list = self._original_get_app_list(request, app_label=app_label)

    # ─── حذف اپ‌های مخفی ───
    app_list = [
        app for app in app_list
        if app["app_label"] not in HIDDEN_APPS
    ]

    # ─── مرتب‌سازی ───
    order_map = {
        label: idx
        for idx, label in enumerate(VISIBLE_APPS_ORDER)
    }
    app_list.sort(
        key=lambda app: order_map.get(app["app_label"], 999)
    )

    return app_list


def patch_admin_site() -> None:
    """
    Override get_app_list روی admin.site.

    ─── نکته: ───
    این تابع توی `apps.core.apps.CoreConfig.ready()` صدا زده میشه.
    """
    # ─── فقط یه بار patch کن ───
    if hasattr(admin.site, "_original_get_app_list"):
        return

    admin.site._original_get_app_list = admin.site.get_app_list
    admin.site.get_app_list = _custom_get_app_list.__get__(admin.site)

    logger.debug("Admin site patched: get_app_list overridden")