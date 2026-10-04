"""
تنظیمات پایه پروژه آرایشیار.

این فایل شامل تنظیمات مشترک بین همه‌ی محیط‌هاست.
تنظیمات مخصوص dev یا prod توی فایل‌های dev.py و prod.py هستن.

منبع متغیرها: فایل .env (با django-environ)
"""

from pathlib import Path

import environ

# ═══════════════════════════════════════════════════════════════
#  مسیرهای پایه
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ═══════════════════════════════════════════════════════════════
#  خواندن متغیرهای محیطی از .env
# ═══════════════════════════════════════════════════════════════

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    LANGUAGE_CODE=(str, "fa-ir"),
    TIME_ZONE=(str, "Asia/Tehran"),
    SITE_ID=(int, 1),
    SITE_DOMAIN=(str, "localhost:8000"),
    SITE_NAME=(str, "آرایشیار"),
    SMS_BACKEND=(str, "apps.notifications.backends.console.ConsoleSMSBackend"),
    KAVENEGAR_API_KEY=(str, ""),
    KAVENEGAR_SENDER=(str, ""),
    OTP_LENGTH=(int, 6),
    OTP_EXPIRY_MINUTES=(int, 2),
    OTP_MAX_ATTEMPTS=(int, 5),
    OTP_RATE_LIMIT_PER_HOUR=(int, 5),
    SECURE_SSL_REDIRECT=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    MAX_UPLOAD_SIZE_MB=(int, 2),
    LOG_LEVEL=(str, "INFO"),
    PAYMENT_CARD_NUMBER=(str, "6219-8619-0627-4690"),
    PAYMENT_CARD_OWNER=(str, "آرایشیار"),
    PAYMENT_CARD_BANK=(str, "بانک سامان"),
    SUPPORT_PHONE=(str, "09127516317"),
    SUPPORT_WHATSAPP=(str, "989127516317"),
    SUPPORT_TELEGRAM=(str, "arayeshyar_support"),
    SMSIR_API_KEY=(str, ""),
    SMSIR_LINE_NUMBER=(str, ""),
    SMSIR_TEMPLATE_ID=(int, 0),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    env.read_env(str(env_file))

# ═══════════════════════════════════════════════════════════════
#  امنیت
# ═══════════════════════════════════════════════════════════════

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# ═══════════════════════════════════════════════════════════════
#  اپلیکیشن‌ها
# ═══════════════════════════════════════════════════════════════

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "django_htmx",
    "template_partials",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.business",
    "apps.booking",
    "apps.customers",
    "apps.notifications",
    "apps.analytics",
    "apps.support",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ═══════════════════════════════════════════════════════════════
#  میدل‌ور
# ═══════════════════════════════════════════════════════════════

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

# ═══════════════════════════════════════════════════════════════
#  URL / WSGI / ASGI
# ═══════════════════════════════════════════════════════════════

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ═══════════════════════════════════════════════════════════════
#  قالب‌ها
# ═══════════════════════════════════════════════════════════════

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.tz",
                "apps.core.context_processors.user_context",
                "apps.core.context_processors.site_context",
            ],
            "builtins": [
                "apps.core.templatetags.jalali",
            ],
        },
    },
]

# ═══════════════════════════════════════════════════════════════
#  دیتابیس
# ═══════════════════════════════════════════════════════════════

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# ═══════════════════════════════════════════════════════════════
#  Cache
# ═══════════════════════════════════════════════════════════════

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "arayeshyar-default",
    },
}

# ═══════════════════════════════════════════════════════════════
#  احراز هویت
# ═══════════════════════════════════════════════════════════════

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.OTPBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "accounts:login_phone"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# ═══════════════════════════════════════════════════════════════
#  اعتبارسنجی رمز عبور
# ═══════════════════════════════════════════════════════════════

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ═══════════════════════════════════════════════════════════════
#  زبان و زمان
# ═══════════════════════════════════════════════════════════════

LANGUAGE_CODE = env("LANGUAGE_CODE")
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

# ═══════════════════════════════════════════════════════════════
#  فایل‌های استاتیک
# ═══════════════════════════════════════════════════════════════

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ═══════════════════════════════════════════════════════════════
#  فایل‌های Media (آپلود)
# ═══════════════════════════════════════════════════════════════

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

MAX_UPLOAD_SIZE_MB = env("MAX_UPLOAD_SIZE_MB")
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# ═══════════════════════════════════════════════════════════════
#  Session
# ═══════════════════════════════════════════════════════════════

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "arayeshyar_sessionid"
SESSION_COOKIE_PATH = "/"

# ═══════════════════════════════════════════════════════════════
#  CSRF
# ═══════════════════════════════════════════════════════════════

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = "arayeshyar_csrftoken"
CSRF_COOKIE_PATH = "/"
CSRF_FAILURE_VIEW = "apps.core.views.csrf_failure"

# ═══════════════════════════════════════════════════════════════
#  Messages
# ═══════════════════════════════════════════════════════════════

from django.contrib.messages import constants as messages  # noqa: E402

MESSAGE_TAGS = {
    messages.DEBUG: "info",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}

# ═══════════════════════════════════════════════════════════════
#  Site
# ═══════════════════════════════════════════════════════════════

SITE_ID = env("SITE_ID")
SITE_DOMAIN = env("SITE_DOMAIN")
SITE_NAME = env("SITE_NAME")

# ═══════════════════════════════════════════════════════════════
#  Admin Branding
# ═══════════════════════════════════════════════════════════════

ADMIN_SITE_HEADER = "پنل مدیریت آرایشیار"
ADMIN_SITE_TITLE = "آرایشیار"
ADMIN_INDEX_TITLE = "به پنل مدیریت آرایشیار خوش آمدید"

# ═══════════════════════════════════════════════════════════════
#  Payment Info
# ═══════════════════════════════════════════════════════════════

PAYMENT_CARD_NUMBER = env.str("PAYMENT_CARD_NUMBER", default="6219-8619-0627-4690")
PAYMENT_CARD_OWNER = env.str("PAYMENT_CARD_OWNER", default="آرایشیار")
PAYMENT_CARD_BANK = env.str("PAYMENT_CARD_BANK", default="بانک ملی")

# ═══════════════════════════════════════════════════════════════
#  OTP
# ═══════════════════════════════════════════════════════════════

OTP_LENGTH = env("OTP_LENGTH")
OTP_EXPIRY_MINUTES = env("OTP_EXPIRY_MINUTES")
OTP_MAX_ATTEMPTS = env("OTP_MAX_ATTEMPTS")
OTP_RATE_LIMIT_PER_HOUR = env("OTP_RATE_LIMIT_PER_HOUR")

# ═══════════════════════════════════════════════════════════════
#  SMS Backend
# ═══════════════════════════════════════════════════════════════

SMS_BACKEND = env("SMS_BACKEND")
KAVENEGAR_API_KEY = env("KAVENEGAR_API_KEY")
KAVENEGAR_SENDER = env("KAVENEGAR_SENDER")

# ═══════════════════════════════════════════════════════════════
#  سایر
# ═══════════════════════════════════════════════════════════════

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ═══════════════════════════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════════════════════════

LOG_LEVEL = env("LOG_LEVEL")

# ─── مسیر لاگ‌ها (توی production read-only، خطا نمیده) ───
LOG_DIR = BASE_DIR / "logs"
try:
    LOG_DIR.mkdir(exist_ok=True)
except (OSError, PermissionError):
    pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "arayeshyar.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
            "delay": True,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "errors.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "ERROR",
            "encoding": "utf-8",
            "delay": True,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file", "error_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# ═══════════════════════════════════════════════════════════════
#  HTMX
# ═══════════════════════════════════════════════════════════════

DJANGO_HTMX_HTTP_RESPONSE_ERRORS = True

# ═══════════════════════════════════════════════════════════════
#  Support Info
# ═══════════════════════════════════════════════════════════════

SUPPORT_PHONE = env("SUPPORT_PHONE")
SUPPORT_WHATSAPP = env("SUPPORT_WHATSAPP")
SUPPORT_TELEGRAM = env("SUPPORT_TELEGRAM")

# SMS.ir
SMSIR_API_KEY = env("SMSIR_API_KEY")
SMSIR_LINE_NUMBER = env("SMSIR_LINE_NUMBER")
SMSIR_TEMPLATE_ID = env("SMSIR_TEMPLATE_ID")