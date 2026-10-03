"""AppConfig برای analytics."""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    verbose_name = "آمار"
    verbose_name_plural = "آمار"