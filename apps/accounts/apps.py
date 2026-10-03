"""AppConfig برای accounts."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "حساب‌های کاربری"
    verbose_name_plural = "حساب‌های کاربری"

    def ready(self) -> None:
        """Signal ها رو لود کن."""
        from . import signals  # noqa: F401