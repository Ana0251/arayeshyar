"""
WSGI config پروژه آرایشیار.

برای اجرا در production با gunicorn:
    gunicorn config.wsgi:application --bind 0.0.0.0:8000
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# ─── اضافه کردن ریشه پروژه به sys.path ───
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# ─── تنظیمات Django (config.settings خودش dev/prod رو انتخاب می‌کنه) ───
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()