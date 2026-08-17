import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("edu_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# TZ 5.8: ikki queue — default va media
app.conf.task_routes = {
    "apps.courses.tasks.*": {"queue": "media"},
    "apps.notifications.tasks.*": {"queue": "default"},
    "apps.payments.tasks.*": {"queue": "default"},
    "apps.certificates.tasks.*": {"queue": "default"},
    "apps.analytics.tasks.*": {"queue": "default"},
}
