"""TZ 5.4 (Event, DailyAggregate, Report), AD-05, TE-03, 5.12 (KPI)."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Event(BaseModel):
    """Xom hodisa jurnali — GA4 (I-08) bilan parallel, ichki hisobotlar uchun."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )
    event_type = models.CharField(max_length=100, db_index=True)  # masalan "lesson_view", "checkout_started"
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "analytics_event"
        indexes = [models.Index(fields=["event_type", "created_at"])]


class DailyAggregate(BaseModel):
    """Kechasi 03:00 hisoblanadi (5.8) — DAU/MAU, daromad va h.k. tez o'qish uchun."""

    date = models.DateField(db_index=True)
    metric = models.CharField(max_length=100)  # "dau", "mau", "revenue", "new_registrations"
    dimension = models.JSONField(default=dict, blank=True)  # masalan {"course_id": "..."}
    value = models.FloatField(default=0)

    class Meta:
        db_table = "analytics_daily_aggregate"
        constraints = [
            models.UniqueConstraint(fields=["date", "metric", "dimension"], name="uniq_daily_metric"),
        ]
