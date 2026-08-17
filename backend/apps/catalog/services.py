from apps.audit.services import log_action
from apps.catalog.models import Review, ReviewStatus
from apps.core.exceptions import DomainError


def submit_review(*, user, course, rating: int, comment: str = "") -> Review:
    """K-08: faqat kursni sotib olganlar yozadi, moderatsiyadan keyin nashr etiladi."""
    from apps.enrollment.selectors import has_active_enrollment

    if not has_active_enrollment(user=user, course=course):
        raise DomainError("Sharh qoldirish uchun avval kursni sotib olishingiz kerak", code="not_enrolled")
    if not (1 <= rating <= 5):
        raise DomainError("Baho 1 dan 5 gacha bo'lishi kerak", code="invalid_rating")

    review, _ = Review.objects.update_or_create(
        course=course, user=user,
        defaults={"rating": rating, "comment": comment, "status": ReviewStatus.PENDING},
    )
    return review


def moderate_review(*, actor, review: Review, approve: bool) -> Review:
    before = {"status": review.status}
    review.status = ReviewStatus.PUBLISHED if approve else ReviewStatus.REJECTED
    review.save(update_fields=["status"])
    log_action(actor=actor, action="review.moderate", obj=review, before=before, after={"status": review.status})

    if approve:
        _recalculate_course_rating(review.course)
    return review


def _recalculate_course_rating(course) -> None:
    from django.db.models import Avg, Count

    agg = Review.objects.filter(course=course, status=ReviewStatus.PUBLISHED).aggregate(
        avg=Avg("rating"), count=Count("id"),
    )
    course.rating_avg = agg["avg"] or 0
    course.rating_count = agg["count"] or 0
    course.save(update_fields=["rating_avg", "rating_count"])
