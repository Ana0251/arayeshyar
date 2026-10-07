"""
تنظیمات محیط Production (تولید).

تفاوت‌ها با development:
- DEBUG = False
- ALLOWED_HOSTS محدود
- HTTPS اجباری
- HSTS فعال
- لاگ فقط به console (چون فایل‌سیستم read-only هست)
"""

from .base import *  # noqa: F401,F403

# ═══════════════════════════════════════════════════════════════
#  Debug
# ═══════════════════════════════════════════════════════════════

DEBUG = False

# ─── ALLOWED_HOSTS از .env میاد ───

# ═══════════════════════════════════════════════════════════════
#  امنیت HTTPS
# ═══════════════════════════════════════════════════════════════

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ─── HSTS ───
# ─── نکته: برای اولین deploy، مقدار کم بذار (۱ روز) ───
# ─── بعد از پایداری، زیادش کن ───
SECURE_HSTS_SECONDS = 60 * 60 * 24  # ۱ روز (بعداً ۱ سال کن)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ─── Proxy (Liara پشت proxy هستیم) ───
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


USE_X_FORWARDED_HOST = True

# ─── این هم خوبه: از X-Forwarded-Port استفاده کنه ───
USE_X_FORWARDED_PORT = True

# ═══════════════════════════════════════════════════════════════
#  Email (SMTP واقعی)
# ═══════════════════════════════════════════════════════════════

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

# ═══════════════════════════════════════════════════════════════
#  Caching (اختیاری — Redis)
# ═══════════════════════════════════════════════════════════════

# اگه Liara Redis داری، اینا رو uncomment کن:
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.redis.RedisCache",
#         "LOCATION": env("REDIS_URL"),
#     }
# }

# ═══════════════════════════════════════════════════════════════
#  Sentry (اختیاری)
# ═══════════════════════════════════════════════════════════════

# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
#
# SENTRY_DSN = env("SENTRY_DSN", default="")
# if SENTRY_DSN:
#     sentry_sdk.init(
#         dsn=SENTRY_DSN,
#         integrations=[DjangoIntegration()],
#         traces_sample_rate=0.1,
#         send_default_pii=False,
#     )

# ═══════════════════════════════════════════════════════════════
#  Logging (production — فقط console)
# ═══════════════════════════════════════════════════════════════
#
# ─── نکته مهم: ───
# توی Liara، فایل‌سیستم read-only هست. پس فقط console.
# لاگ‌ها از طریق `liara logs` یا پنل Liara قابل مشاهده‌ست.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}