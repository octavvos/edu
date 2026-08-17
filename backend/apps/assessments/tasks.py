from celery import shared_task
from django.utils import timezone


@shared_task
def expire_overdue_attempts():
    """T-03: taymer tugagan lekin yopilmagan urinishlarni avtomatik yakunlaydi."""
    from apps.assessments.models import Attempt, AttemptStatus
    from apps.assessments.services import finalize_attempt

    qs = Attempt.objects.filter(
        status=AttemptStatus.IN_PROGRESS, expires_at__isnull=False, expires_at__lte=timezone.now(),
    )
    count = 0
    for attempt in qs:
        finalize_attempt(attempt=attempt)
        count += 1
    return f"{count} ta urinish avtomatik yakunlandi"
