"""AppConfig برای business."""

from django.apps import AppConfig


class BusinessConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.business"
    verbose_name = "کسب‌وکارها"
    verbose_name_plural = "کسب‌وکارها"

    def ready(self) -> None:
        """Signal ها رو لود کن."""
        from . import signals  # noqa: F401