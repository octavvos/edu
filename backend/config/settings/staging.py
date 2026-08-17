from .base import *  # noqa: F403
from .base import env

DEBUG = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("SENDGRID_SMTP_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("SENDGRID_USERNAME", default="apikey")
EMAIL_HOST_PASSWORD = env("SENDGRID_API_KEY", default="")

SMS_BACKEND = "apps.notifications.backends.sms.EskizSmsBackend"

SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        environment="staging",
        traces_sample_rate=0.2,
    )
