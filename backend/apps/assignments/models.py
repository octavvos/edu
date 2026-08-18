"""TZ 4.7 (H01-H06) — uy vazifalari va baholash."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, i18n_field


class Homework(BaseModel):
    """
    Mentor guruhga jo'natgan vazifa. Bitta dars bir nechta guruhga
    jo'natilishi mumkin — har biri o'z muddati va topshirig'i bilan,
    shuning uchun kalit (dars, guruh) juftligi.
    """

    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="homeworks")
    group = models.ForeignKey("groups.Group", on_delete=models.CASCADE, related_name="homeworks")
    instructions = i18n_field()
    deadline_at = models.DateTimeField(null=True, blank=True)  # H-05
    max_score = models.PositiveSmallIntegerField(default=100)
    # Mentor "jo'natish"da tanlagan material (taqdimot yoki vazifa fayli) —
    # shu darsning materiallaridan biri, ixtiyoriy.
    material = models.ForeignKey(
        "courses.FileAsset", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )

    class Meta:
        db_table = "assignments_homework"
        constraints = [
            models.UniqueConstraint(fields=["lesson", "group"], name="uniq_homework_per_lesson_group"),
        ]
        indexes = [models.Index(fields=["group"])]


class SubmissionStatus(models.TextChoices):
    """H-03: yuborilgan -> tekshirilmoqda -> qayta ishlashga qaytarildi -> qabul qilindi."""

    SUBMITTED = "submitted", "Yuborilgan"
    UNDER_REVIEW = "under_review", "Tekshirilmoqda"
    NEEDS_REVISION = "needs_revision", "Qayta ishlashga qaytarildi"
    ACCEPTED = "accepted", "Qabul qilindi"


class Submission(BaseModel):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    enrollment = models.ForeignKey("enrollment.Enrollment", on_delete=models.CASCADE, related_name="submissions")
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_submissions",
    )  # H-02

    file = models.FileField(upload_to="submissions/", null=True, blank=True)  # H-01
    text = models.TextField(blank=True)
    link = models.URLField(blank=True)

    status = models.CharField(max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.SUBMITTED)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)  # H-05

    class Meta:
        db_table = "assignments_submission"
        indexes = [models.Index(fields=["mentor", "status"])]
        ordering = ["-submitted_at"]


class Grade(BaseModel):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="grade")
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    score = models.PositiveSmallIntegerField()  # H-04: 0-100
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignments_grade"
        constraints = [
            models.CheckConstraint(condition=models.Q(score__gte=0) & models.Q(score__lte=100), name="grade_score_range"),
        ]
