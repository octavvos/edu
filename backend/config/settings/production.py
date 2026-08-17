from .staging import *  # noqa: F403 — production staging bilan bir xil, faqat muhit nomi farq qiladi
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

if globals().get("SENTRY_DSN"):
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,  # noqa: F405
        environment="production",
        traces_sample_rate=0.1,
    )
