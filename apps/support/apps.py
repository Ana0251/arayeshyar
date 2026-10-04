"""AppConfig برای support."""

from django.apps import AppConfig


class SupportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.support"
    verbose_name = "پشتیبانی"
    verbose_name_plural = "پشتیبانی"