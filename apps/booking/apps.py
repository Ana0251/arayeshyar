"""AppConfig برای booking."""

from django.apps import AppConfig


class BookingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.booking"
    verbose_name = "نوبت‌دهی"
    verbose_name_plural = "نوبت‌دهی"