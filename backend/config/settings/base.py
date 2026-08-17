"""
Base Django settings — shared by local / staging / production.
Ma'lumot manbai: TZ 5.2 (Texnologiyalar steki), 5.4 (loyiha strukturasi),
5.5.1 (D01-D12 — kelajakka tayyorlik qarorlari).
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_celery_beat",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "waffle",
    "django_filters",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.rbac",
    "apps.audit",
    "apps.catalog",
    "apps.courses",
    "apps.enrollment",
    "apps.assessments",
    "apps.assignments",
    "apps.certificates",
    "apps.payments",
    "apps.payouts",
    "apps.notifications",
    "apps.communication",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "apps.audit.middleware.RequestContextMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL 16 (TZ 5.2)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://edu:edu@localhost:5432/edu"),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ---------------------------------------------------------------------------
# Password validation — A-01: min 8, Argon2 hashing
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "apps.accounts.validators.PasswordComplexityValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# ---------------------------------------------------------------------------
# Internationalization — TZ 4.13 (L01-L04)
# Interfeys: uz (lotin), ru. Kontent i18n JSONB: uz, uz_cyrl, ru, en.
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "uz"
LANGUAGES = [
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
]
CONTENT_LANGUAGES = ["uz", "uz_cyrl", "ru", "en"]
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "UTC"  # D-10: barcha vaqtlar UTC'da
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# DRF (TZ 5.6 — API dizayni)
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.CursorSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "EXCEPTION_HANDLER": "apps.core.exceptions.rfc7807_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        # A-07 / 5.6: anonim 60/min, auth 300/min, OTP alohida (accounts/throttles.py)
        "anon": "60/min",
        "user": "300/min",
        "otp": "3/hour",
    },
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    # A-02: access 15 daqiqa, refresh 30 kun, rotation
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,  # A-03: qayta ishlatilgan refresh -> oila bekor
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Onlayn ta'lim platformasi API",
    "DESCRIPTION": "MVP — TZ v3.0 asosida",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
}

# ---------------------------------------------------------------------------
# Celery / Redis (TZ 5.2, 5.8)
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_DEFAULT_QUEUE = "default"

# TZ 5.8 — Beat jadvali. DatabaseScheduler birinchi ishga tushganda shu
# yozuvlarni PeriodicTask jadvaliga import qiladi; keyinchalik admin
# paneldan (AD-07) tahrirlash mumkin.
CELERY_BEAT_SCHEDULE = {
    "poll-pending-payments": {
        "task": "apps.payments.tasks.poll_pending_payments",
        "schedule": timedelta(minutes=10),
    },
    "send-deadline-reminders": {
        "task": "apps.assignments.tasks.send_deadline_reminders",
        "schedule": timedelta(minutes=15),
    },
    "close-expired-enrollments": {
        "task": "apps.enrollment.tasks.close_expired_enrollments",
        "schedule": timedelta(days=1),
    },
    "compute-daily-aggregates": {
        "task": "apps.analytics.tasks.compute_daily_aggregates",
        "schedule": timedelta(days=1),  # ideal holda crontab(hour=3, minute=0)
    },
    "reconcile-payments": {
        "task": "apps.payments.tasks.reconcile_payments_with_provider",
        "schedule": timedelta(days=1),
    },
    "cleanup-expired-otp": {
        "task": "apps.accounts.tasks.cleanup_expired_otp_codes",
        "schedule": timedelta(days=1),
    },
    "anonymize-expired-deletions": {
        "task": "apps.accounts.tasks.anonymize_expired_deletion_requests",
        "schedule": timedelta(days=1),
    },
    "expire-overdue-quiz-attempts": {
        "task": "apps.assessments.tasks.expire_overdue_attempts",
        "schedule": timedelta(minutes=5),
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# ---------------------------------------------------------------------------
# Storage — MinIO / S3-compatible (D-08: S3, local disk emas)
# ---------------------------------------------------------------------------
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
AWS_ACCESS_KEY_ID = env("MINIO_ACCESS_KEY", default="minioadmin")
AWS_SECRET_ACCESS_KEY = env("MINIO_SECRET_KEY", default="minioadmin")
AWS_STORAGE_BUCKET_NAME = env("MINIO_BUCKET", default="edu-platform")
AWS_S3_ENDPOINT_URL = env("MINIO_ENDPOINT", default="http://localhost:9000")
AWS_S3_ADDRESSING_STYLE = "path"
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 900  # V-06: signed URL TTL <= 15 daqiqa

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Xavfsizlik (TZ 5.11)
# ---------------------------------------------------------------------------
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# Tashqi integratsiyalar (TZ 7-bo'lim)
# ---------------------------------------------------------------------------
ESKIZ_EMAIL = env("ESKIZ_EMAIL", default="")
ESKIZ_PASSWORD = env("ESKIZ_PASSWORD", default="")

PAYME_MERCHANT_ID = env("PAYME_MERCHANT_ID", default="")
PAYME_SECRET_KEY = env("PAYME_SECRET_KEY", default="")
PAYME_TEST_MODE = env.bool("PAYME_TEST_MODE", default=True)

BUNNY_STREAM_LIBRARY_ID = env("BUNNY_STREAM_LIBRARY_ID", default="")
BUNNY_STREAM_API_KEY = env("BUNNY_STREAM_API_KEY", default="")
BUNNY_STREAM_CDN_HOSTNAME = env("BUNNY_STREAM_CDN_HOSTNAME", default="")

FCM_SERVER_KEY = env("FCM_SERVER_KEY", default="")

CLOUDFLARE_TURNSTILE_SECRET = env("CLOUDFLARE_TURNSTILE_SECRET", default="")

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:3000")

# ---------------------------------------------------------------------------
# Domain-specific defaults — feature flags / business rules
# ---------------------------------------------------------------------------
PLATFORM_COMMISSION_PERCENT = env.int("PLATFORM_COMMISSION_PERCENT", default=30)  # P-07
MAX_ACTIVE_DEVICES = env.int("MAX_ACTIVE_DEVICES", default=3)  # A-09
OTP_TTL_SECONDS = 120  # A-04
OTP_MAX_ATTEMPTS = 3
OTP_MAX_PER_HOUR = 3
SIGNED_URL_TTL_SECONDS = 900  # V-06
ENROLLMENT_ACCESS_DEFAULT_DAYS = None  # None = lifetime access to purchased course

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"level":"%(levelname)s","time":"%(asctime)s",'
            '"logger":"%(name)s","message":"%(message)s"}',
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
