#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

─── انتخاب settings: ───
پیش‌فرض: config.settings (که خودش بر اساس DJANGO_ENV تصمیم می‌گیره)
اگه DJANGO_SETTINGS_MODULE از قبل ست شده باشه، از همون استفاده میشه.
"""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    # ─── تنظیمات از config.settings (که خودش dev/prod رو انتخاب می‌کنه) ───
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()