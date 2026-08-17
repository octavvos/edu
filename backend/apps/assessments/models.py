"""TZ 4.6 (T01-T07) — testlar."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, i18n_field


class ResultDisplayMode(models.TextChoices):
    IMMEDIATE = "immediate", "Darhol"
    AFTER_TEST = "after_test", "Testdan keyin"
    NEVER = "never", "Hech qachon"


class Quiz(BaseModel):
    lesson = models.OneToOneField("courses.Lesson", on_delete=models.CASCADE, related_name="quiz")

    time_limit_seconds = models.PositiveIntegerField(null=True, blank=True)  # T-03
    questions_per_attempt = models.PositiveIntegerField(null=True, blank=True)  # T-01 (masalan 100 dan 20)
    randomize_questions = models.BooleanField(default=True)  # T-02
    randomize_choices = models.BooleanField(default=True)  # T-02

    max_attempts = models.PositiveIntegerField(default=1)  # T-04
    pass_percent = models.PositiveSmallIntegerField(default=60)  # T-04
    retake_cooldown_hours = models.PositiveIntegerField(default=0)  # T-04
    result_display = models.CharField(max_length=20, choices=ResultDisplayMode.choices, default=ResultDisplayMode.AFTER_TEST)  # T-05

    class Meta:
        db_table = "assessments_quiz"


class QuestionType(models.TextChoices):
    """4.6-band: 4 ta savol turi."""

    SINGLE_CHOICE = "single_choice", "Bitta to'g'ri javob"
    MULTIPLE_CHOICE = "multiple_choice", "Bir nechta to'g'ri javob"
    TRUE_FALSE = "true_false", "To'g'ri/noto'g'ri"
    SHORT_TEXT = "short_text", "Qisqa matnli javob"


class Question(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    type = models.CharField(max_length=20, choices=QuestionType.choices)
    text = i18n_field()
    explanation = i18n_field()  # T-06: noto'g'ri javob uchun izoh
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    # SHORT_TEXT uchun: aniq moslik yoki regex
    correct_text_pattern = models.CharField(max_length=255, blank=True)
    is_regex = models.BooleanField(default=False)

    class Meta:
        db_table = "assessments_question"
        ordering = ["order"]


class Choice(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = i18n_field()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "assessments_choice"
        ordering = ["order"]


class AttemptStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "Jarayonda"
    SUBMITTED = "submitted", "Yuborilgan"
    EXPIRED = "expired", "Vaqti tugagan"


class Attempt(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    enrollment = models.ForeignKey("enrollment.Enrollment", on_delete=models.CASCADE, related_name="quiz_attempts")

    status = models.CharField(max_length=20, choices=AttemptStatus.choices, default=AttemptStatus.IN_PROGRESS)
    question_ids = models.JSONField(default=list)  # T-01/T-02: shu urinish uchun tanlangan/aralashtirilgan savollar
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # T-03: server-side taymer

    score_percent = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True)

    class Meta:
        db_table = "assessments_attempt"
        indexes = [models.Index(fields=["user", "quiz"])]


class Answer(BaseModel):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="+")
    selected_choice_ids = models.JSONField(default=list, blank=True)
    text_answer = models.CharField(max_length=500, blank=True)
    is_correct = models.BooleanField(null=True)
    points_awarded = models.FloatField(default=0)

    class Meta:
        db_table = "assessments_answer"
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="uniq_attempt_question_answer"),
        ]
