"""
تنظیمات محیط Production (تولید).

تفاوت‌ها با development:
- DEBUG = False
- ALLOWED_HOSTS محدود
- HTTPS اجباری
- HSTS فعال
- ایمیل واقعی
- Sentry (اختیاری)
"""

from .base import *  # noqa: F401,F403

# ═══════════════════════════════════════════════════════════════
#  Debug
# ═══════════════════════════════════════════════════════════════

DEBUG = False

# ─── ALLOWED_HOSTS از .env میاد ───
# باید دامنه‌ی واقعی رو توی .env بذاری

# ═══════════════════════════════════════════════════════════════
#  امنیت HTTPS
# ═══════════════════════════════════════════════════════════════

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ─── HSTS (HTTP Strict Transport Security) ───
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # ۱ سال
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ─── Proxy (برای Liara که پشت proxy هستیم) ───
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ═══════════════════════════════════════════════════════════════
#  Email (SMTP واقعی)
# ═══════════════════════════════════════════════════════════════

# اگه بعداً ایمیل واقعی خواستی، اینا رو از .env بخون:
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = env("EMAIL_HOST")
# EMAIL_PORT = env.int("EMAIL_PORT", 587)
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = env("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

# ═══════════════════════════════════════════════════════════════
#  Caching (اختیاری)
# ═══════════════════════════════════════════════════════════════

# فعلاً از LocMemCache استفاده می‌کنیم. بعداً Redis اضافه کن:
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": env("REDIS_URL"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#     }
# }

# ═══════════════════════════════════════════════════════════════
#  Sentry (اختیاری — برای error tracking)
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
#  Logging (production)
# ═══════════════════════════════════════════════════════════════

# ─── در production: WARNING+ برای django، INFO+ برای apps ───
LOGGING["root"]["level"] = "WARNING"                    # noqa: F405
LOGGING["loggers"]["django"]["level"] = "WARNING"       # noqa: F405
LOGGING["loggers"]["django.security"]["level"] = "WARNING"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "INFO"            # noqa: F405

