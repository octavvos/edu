"""D-07: payments -> enrollment bog'lanishi faqat event orqali (aylanma import yo'q)."""

from apps.core import events


@events.on(events.EVENT_PAYMENT_SUCCEEDED)
def _on_payment_succeeded(user_id: str, course_id: str, order_id: str, **kwargs):
    from apps.accounts.models import User
    from apps.courses.models import Course
    from apps.enrollment.services import enroll_from_payment

    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)
    enroll_from_payment(user=user, course=course, order_id=order_id)
