"""TZ 4.8 (G01-G06), 5.5, 5.7 — enrollment, progress, drip access."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class AccessType(models.TextChoices):
    PURCHASED = "purchased", "Sotib olingan"
    FREE = "free", "Bepul"
    GIFTED = "gifted", "Sovg'a qilingan"
    ADMIN_GRANTED = "admin_granted", "Admin tomonidan berilgan"


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    EXPIRED = "expired", "Muddati tugagan"
    CANCELLED = "cancelled", "Bekor qilingan"
    REFUNDED = "refunded", "Qaytarilgan"


class Enrollment(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="enrollments")
    course_version = models.ForeignKey(
        "courses.CourseVersion", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )
    access_type = models.CharField(max_length=20, choices=AccessType.choices, default=AccessType.PURCHASED)
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)

    starts_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # None = muddatsiz

    # G-02: denormalizatsiya — tez o'qish uchun
    progress_percent = models.FloatField(default=0)
    completed_lessons_count = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "enrollment_enrollment"
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="uniq_user_course_enrollment"),
        ]
        indexes = [models.Index(fields=["user", "status"])]

    @property
    def is_active(self) -> bool:
        from django.utils import timezone

        if self.status != EnrollmentStatus.ACTIVE:
            return False
        return not self.expires_at or self.expires_at > timezone.now()


class ProgressStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Boshlanmagan"
    IN_PROGRESS = "in_progress", "Jarayonda"
    COMPLETED = "completed", "Tugatilgan"


class Progress(BaseModel):
    """5.7: pleyer har 60 sekundda flush qiladi — har heartbeat uchun alohida INSERT emas."""

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="progress_records")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="+")
    status = models.CharField(max_length=20, choices=ProgressStatus.choices, default=ProgressStatus.NOT_STARTED)
    seconds_watched = models.PositiveIntegerField(default=0)
    last_position = models.PositiveIntegerField(default=0)  # video uchun soniyada
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "enrollment_progress"
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "lesson"], name="uniq_enrollment_lesson"),
        ]
        indexes = [models.Index(fields=["enrollment", "status"])]


class LessonNote(BaseModel):
    """/api/v1/learn/.../notes — foydalanuvchining shaxsiy eslatmalari."""

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="notes")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="+")
    text = models.TextField()
    video_timestamp_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "enrollment_lesson_note"
        ordering = ["-created_at"]
