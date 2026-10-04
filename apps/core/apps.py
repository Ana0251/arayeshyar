"""AppConfig برای core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "هسته"
    verbose_name_plural = "هسته"

    def ready(self) -> None:
        """
        تنظیمات startup:
        - Override سراسری DateInput و TimeInput
        - Admin branding
        - Admin site patch (مخفی‌کردن اپ‌های خالی)
        """
        # ─── HEIF/HEIC support ───
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass
        # ═══════════════════════════════════════════════════════════
        #  Override DateInput / TimeInput
        # ═══════════════════════════════════════════════════════════
        from django import forms

        from .widgets import JalaliDateInput, JalaliTimeInput

        forms.DateInput = JalaliDateInput
        forms.widgets.DateInput = JalaliDateInput
        forms.TimeInput = JalaliTimeInput
        forms.widgets.TimeInput = JalaliTimeInput

        # ═══════════════════════════════════════════════════════════
        #  Admin Branding
        # ═══════════════════════════════════════════════════════════
        from django.conf import settings
        from django.contrib import admin

        admin.site.site_header = getattr(
            settings,
            "ADMIN_SITE_HEADER",
            "پنل مدیریت",
        )
        admin.site.site_title = getattr(
            settings,
            "ADMIN_SITE_TITLE",
            "آرایشیار",
        )
        admin.site.index_title = getattr(
            settings,
            "ADMIN_INDEX_TITLE",
            "به پنل مدیریت خوش آمدید",
        )

        # ═══════════════════════════════════════════════════════════
        #  Admin Site Patch (مخفی‌کردن اپ‌های خالی)
        # ═══════════════════════════════════════════════════════════
        from .admin_site import patch_admin_site

        patch_admin_site()