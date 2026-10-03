"""AppConfig برای customers."""

from django.apps import AppConfig


class CustomersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.customers"
    verbose_name = "مشتری‌ها"
    verbose_name_plural = "مشتری‌ها"

    def ready(self) -> None:
        """Signal ها رو لود کن."""
        from . import signals  # noqa: F401