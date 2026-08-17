"""AD-08: Audit-log — kim, qachon, nimani o'zgartirdi (before/after), append-only."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class AuditLog(BaseModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100)  # masalan: "user.block", "course.reject"
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["object_type", "object_id"]),
            models.Index(fields=["actor", "created_at"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("AuditLog append-only — mavjud yozuvni o'zgartirib bo'lmaydi")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog append-only — yozuvni o'chirib bo'lmaydi")


class ImpersonationSession(BaseModel):
    """AD-01: impersonate — sabab kiritish majburiy, audit-log bilan."""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="impersonations_made",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="impersonated_by",
    )
    reason = models.TextField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "impersonation_session"
        ordering = ["-started_at"]
