from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task
def send_deadline_reminders():
    """N-04/5.8: deadline yaqinlashdi (24s / 2s) — har 15 daqiqada ishga tushadi."""
    from apps.enrollment.models import Enrollment
    from apps.notifications.models import NotificationEvent
    from apps.notifications.tasks import dispatch_notification

    now = timezone.now()
    windows = {
        NotificationEvent.DEADLINE_24H: (now + timedelta(hours=24), now + timedelta(hours=24, minutes=15)),
        NotificationEvent.DEADLINE_2H: (now + timedelta(hours=2), now + timedelta(hours=2, minutes=15)),
    }
    from apps.assignments.models import Homework

    sent = 0
    for event, (start, end) in windows.items():
        homeworks = Homework.objects.filter(deadline_at__gte=start, deadline_at__lt=end)
        for hw in homeworks:
            enrolled_users = Enrollment.objects.filter(
                course=hw.lesson.module.course, status="active",
            ).values_list("user_id", flat=True)
            already_submitted = set(hw.submissions.values_list("user_id", flat=True))
            for user_id in enrolled_users:
                if user_id in already_submitted:
                    continue
                dispatch_notification.delay(
                    user_id=str(user_id), event=event, context={"homework_id": str(hw.id)},
                )
                sent += 1
    return f"{sent} ta deadline eslatmasi yuborildi"
