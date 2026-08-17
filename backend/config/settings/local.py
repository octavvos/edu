from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SMS_BACKEND = "apps.notifications.backends.sms.ConsoleSmsBackend"

# Local dev: signed URLs saqlanmasin, tez-tez o'zgaradi
AWS_QUERYSTRING_AUTH = False

CORS_ALLOW_ALL_ORIGINS = True
