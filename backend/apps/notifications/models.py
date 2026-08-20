"""TZ 4.9 (N01-N05) — kommunikatsiya va bildirishnomalar."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, i18n_field


class NotificationEvent(models.TextChoices):
    """N-04: hodisalar ro'yxati."""

    LESSON_UNLOCKED = "lesson_unlocked", "Yangi dars ochildi"
    DEADLINE_24H = "deadline_24h", "Deadline 24 soat qoldi"
    DEADLINE_2H = "deadline_2h", "Deadline 2 soat qoldi"
    ASSIGNMENT_GRADED = "assignment_graded", "Vazifa tekshirildi"
    HOMEWORK_ASSIGNED = "homework_assigned", "Yangi vazifa yuborildi"
    NEW_COMMENT = "new_comment", "Yangi izoh/javob"
    PAYMENT_SUCCEEDED = "payment_succeeded", "To'lov muvaffaqiyatli"
    CERTIFICATE_READY = "certificate_ready", "Sertifikat tayyor"
    VIDEO_READY = "video_ready", "Video tayyor"
    OTP_CODE = "otp_code", "OTP kod"
    EMAIL_VERIFICATION = "email_verification", "Email tasdiqlash"
    PASSWORD_RESET = "password_reset", "Parolni tiklash"


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In-app"
    PUSH = "push", "Push (FCM)"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"


class NotificationTemplate(BaseModel):
    """N-03: har bir hodisa turi uchun shablon, admin paneldan tahrirlanadi."""

    event = models.CharField(max_length=50, choices=NotificationEvent.choices)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    subject = i18n_field()  # email uchun
    body = i18n_field()  # {"uz": "Salom {{name}}, ...", ...}
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "notifications_template"
        constraints = [
            models.UniqueConstraint(fields=["event", "channel"], name="uniq_template_event_channel"),
        ]


class NotificationPreference(BaseModel):
    """N-03: foydalanuvchi tomonidan yoqib/o'chirish sozlamasi."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_prefs")
    event = models.CharField(max_length=50, choices=NotificationEvent.choices)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "notifications_preference"
        constraints = [
            models.UniqueConstraint(fields=["user", "event", "channel"], name="uniq_user_event_channel"),
        ]


class DispatchStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    SENT = "sent", "Yuborildi"
    FAILED = "failed", "Xatolik"


class NotificationDispatch(BaseModel):
    """N-05: Celery orqali asinxron yuboriladi, muvaffaqiyatsizlikda 3 marta retry."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_dispatches",
        null=True, blank=True,
    )
    event = models.CharField(max_length=50, choices=NotificationEvent.choices)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=DispatchStatus.choices, default=DispatchStatus.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_dispatch"
        indexes = [models.Index(fields=["user", "event"])]
