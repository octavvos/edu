"""
D-07: notifications app boshqa modullarni import qilmaydi — faqat
domain event'larga obuna bo'ladi (apps.core.events). Shu tufayli
payments/certificates/assignments notifications'ni bilmaydi, faqat
event chiqaradi.
"""

from apps.core import events


@events.on(events.EVENT_PAYMENT_SUCCEEDED)
def _on_payment_succeeded(user_id: str, order_id: str, **kwargs):
    from apps.notifications.models import NotificationEvent
    from apps.notifications.tasks import dispatch_notification

    dispatch_notification.delay(
        user_id=user_id, event=NotificationEvent.PAYMENT_SUCCEEDED, context={"order_id": order_id},
    )


@events.on(events.EVENT_CERTIFICATE_ISSUED)
def _on_certificate_issued(user_id: str, certificate_id: str, **kwargs):
    from apps.notifications.models import NotificationEvent
    from apps.notifications.tasks import dispatch_notification

    dispatch_notification.delay(
        user_id=user_id, event=NotificationEvent.CERTIFICATE_READY, context={"certificate_id": certificate_id},
    )


@events.on(events.EVENT_ASSIGNMENT_GRADED)
def _on_assignment_graded(user_id: str, submission_id: str, **kwargs):
    from apps.notifications.models import NotificationEvent
    from apps.notifications.tasks import dispatch_notification

    dispatch_notification.delay(
        user_id=user_id, event=NotificationEvent.ASSIGNMENT_GRADED, context={"submission_id": submission_id},
    )


@events.on(events.EVENT_LESSON_COMPLETED)
def _maybe_notify_next_lesson(user_id: str, enrollment_id: str, lesson_id: str, **kwargs):
    """Drip-content ochilganda N-04 'yangi dars ochildi' bildirishnomasi shu yerdan kelib chiqadi."""
    # Amalga oshirilishi apps.enrollment.services ichida DripRule tekshiruvidan keyin
    # aniq lesson_id bilan alohida chaqiriladi — bu yerda faqat hujjatlash uchun stub.
