"""TZ 4.3 (K01-K09) — kurslar katalogi."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, i18n_field


class Category(BaseModel):
    """K-01: kategoriya va subkategoriyalar (2 daraja)."""

    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children",
    )
    name = i18n_field()
    slug = models.SlugField(max_length=140, unique=True)
    icon = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "catalog_category"
        ordering = ["order", "slug"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.slug

    @property
    def level(self) -> int:
        return 2 if self.parent_id else 1


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Moderatsiyada"
    PUBLISHED = "published", "Nashr etilgan"
    REJECTED = "rejected", "Rad etilgan"


class Review(BaseModel):
    """K-08: faqat kursni sotib olganlar yoza oladi, moderatsiyadan keyin nashr etiladi."""

    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()  # 1-5
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)

    class Meta:
        db_table = "catalog_review"
        constraints = [
            models.UniqueConstraint(fields=["course", "user"], name="uniq_review_per_user_course"),
            models.CheckConstraint(condition=models.Q(rating__gte=1) & models.Q(rating__lte=5), name="review_rating_range"),
        ]
        ordering = ["-created_at"]
