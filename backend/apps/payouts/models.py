"""TZ 4.11 (TE-04), P-07 — o'qituvchi bilan hisob-kitob."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class PayoutStatus(models.TextChoices):
    REQUESTED = "requested", "So'ralgan"
    APPROVED = "approved", "Tasdiqlangan"
    PAID = "paid", "To'landi"
    REJECTED = "rejected", "Rad etilgan"


class PayoutRequest(BaseModel):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payout_requests")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.REQUESTED)
    note = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payouts_payout_request"
        indexes = [models.Index(fields=["teacher", "status"])]
        ordering = ["-created_at"]
