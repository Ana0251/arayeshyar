"""
تنظیمات محیط Development (توسعه).

تفاوت‌ها با production:
- DEBUG = True
- ALLOWED_HOSTS بازتر
- django-extensions فعال
- debug-toolbar (اگه نصب باشه)
- ایمیل به console چاپ میشه
"""

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE  # noqa: F401

# ═══════════════════════════════════════════════════════════════
#  Debug
# ═══════════════════════════════════════════════════════════════

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "*.ngrok.io",
    "*.trycloudflare.com",
]

# ═══════════════════════════════════════════════════════════════
#  CSRF
# ═══════════════════════════════════════════════════════════════

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://*.ngrok.io",
    "https://*.trycloudflare.com",
]

# ═══════════════════════════════════════════════════════════════
#  Cookie (روی HTTP هم کار کنه)
# ═══════════════════════════════════════════════════════════════

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# ═══════════════════════════════════════════════════════════════
#  Email (به console چاپ میشه)
# ═══════════════════════════════════════════════════════════════

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ═══════════════════════════════════════════════════════════════
#  Django Extensions
# ═══════════════════════════════════════════════════════════════

INSTALLED_APPS = INSTALLED_APPS + [
    "django_extensions",
]

# ═══════════════════════════════════════════════════════════════
#  django-debug-toolbar (اختیاری)
# ═══════════════════════════════════════════════════════════════

try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]

    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

    INTERNAL_IPS = ["127.0.0.1", "localhost"]

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    }
except ImportError:
    pass