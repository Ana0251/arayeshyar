"""
تنظیمات پروژه آرایشیار.

این پکیج به سه بخش تقسیم شده:
- base.py  → تنظیمات مشترک
- dev.py   → development (SQLite، DEBUG=True)
- prod.py  → production (PostgreSQL، DEBUG=False)

─── انتخاب محیط: ───
از متغیر محیطی DJANGO_ENV استفاده می‌کنه:

    # Development
    set DJANGO_ENV=dev
    python manage.py runserver

    # Production
    set DJANGO_ENV=prod
    gunicorn config.wsgi

اگه DJANGO_ENV ست نشده باشه، dev پیش‌فرضه.

─── نکته: ───
این فایل باید به‌عنوان DJANGO_SETTINGS_MODULE استفاده بشه
(نه مستقیم config.settings.dev یا config.settings.prod).
مدیریت Django (manage.py, wsgi.py, asgi.py) هم به همین
اشاره می‌کنن تا این logic اجرا بشه.
"""

import os

# ─── انتخاب خودکار settings بر اساس محیط ───
DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev").lower()

if DJANGO_ENV == "prod":
    from .prod import *  # noqa: F401,F403
elif DJANGO_ENV == "dev":
    from .dev import *  # noqa: F401,F403
else:
    raise ValueError(
        f"مقدار DJANGO_ENV نامعتبره: '{DJANGO_ENV}'. "
        f"مقادیر مجاز: 'dev', 'prod'"
    )