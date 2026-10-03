"""AppConfig برای notifications."""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "اعلان‌ها"
    verbose_name_plural = "اعلان‌ها"