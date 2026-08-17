from celery import shared_task
from django.utils import timezone


@shared_task
def close_expired_enrollments():
    """5.8: muddati o'tgan enrollment'larni yopish — kuniga 1 marta."""
    from apps.enrollment.models import Enrollment, EnrollmentStatus

    updated = Enrollment.objects.filter(
        status=EnrollmentStatus.ACTIVE, expires_at__isnull=False, expires_at__lte=timezone.now(),
    ).update(status=EnrollmentStatus.EXPIRED)
    return f"{updated} ta enrollment muddati tugagani sababli yopildi"
