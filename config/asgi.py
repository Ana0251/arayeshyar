"""
ASGI config پروژه آرایشیار.

برای اجرا در production با ASGI server (uvicorn):
    uvicorn config.asgi:application --host 0.0.0.0 --port 8000

برای توسعه:
    python manage.py runserver  (از WSGI استفاده می‌کنه)

اگه بعداً Channels برای WebSocket اضافه کردیم، این فایل
protocol router رو اضافه می‌کنه.
"""

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

# ─── اضافه کردن ریشه پروژه به sys.path ───
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# ─── تنظیمات Django (config.settings خودش dev/prod رو انتخاب می‌کنه) ───
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()