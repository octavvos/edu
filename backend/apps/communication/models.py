"""
TZ 4.9 (N-01) — dars ostida izohlar va Q&A.
Savol/javob bitta threaded `Comment` modeli orqali ifodalanadi: `parent`
bo'sh bo'lsa savol (yoki mustaqil izoh), `parent` to'ldirilsa javob.
Real vaqtdagi chat MVP'ga kirmaydi (v1.2) — REST + davriy yangilanish.
"""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class CommentStatus(models.TextChoices):
    PENDING = "pending", "Moderatsiyada"
    PUBLISHED = "published", "Nashr etilgan"
    HIDDEN = "hidden", "Yashirilgan"


class Comment(BaseModel):
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies",
    )
    text = models.TextField()
    is_question = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=CommentStatus.choices, default=CommentStatus.PUBLISHED)
    helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "communication_comment"
        indexes = [models.Index(fields=["lesson", "parent"])]
        ordering = ["created_at"]


class HelpfulVote(BaseModel):
    """N-01: «foydali» ovozi."""

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")

    class Meta:
        db_table = "communication_helpful_vote"
        constraints = [
            models.UniqueConstraint(fields=["comment", "user"], name="uniq_comment_vote_per_user"),
        ]
