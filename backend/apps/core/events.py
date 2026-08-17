"""
Domain event bus — D-07: modullar bir-birining models/services'iga
to'g'ridan-to'g'ri import qilmaydi, faqat event orqali gaplashadi.

Masalan: payments.services to'lov muvaffaqiyatli bo'lganda
`payment_succeeded` event chiqaradi; enrollment app shu eventga
`@on("payment_succeeded")` bilan obuna bo'lib enrollment ochadi.
Bu ikki modul orasida aylanma bog'liqlikni (circular import) yo'q qiladi.

Sodda, sinxron in-process pub/sub. Agar kelajakda haqiqiy message
broker (masalan Celery task sifatida) kerak bo'lsa, `publish()` ichini
o'zgartirish kifoya — chaqiruvchi kod o'zgarmaydi.
"""

import logging
from collections import defaultdict
from collections.abc import Callable

logger = logging.getLogger(__name__)

_subscribers: dict[str, list[Callable]] = defaultdict(list)


def on(event_name: str):
    """Dekorator: funksiyani event'ga obuna qiladi."""

    def decorator(func: Callable) -> Callable:
        _subscribers[event_name].append(func)
        return func

    return decorator


def publish(event_name: str, **payload) -> None:
    """Eventni barcha obunachilarga sinxron yetkazadi."""
    for handler in _subscribers.get(event_name, []):
        try:
            handler(**payload)
        except Exception:  # noqa: BLE001 — bitta handler xatosi boshqasini to'xtatmasin
            logger.exception("Event handler failed: event=%s handler=%s", event_name, handler)


# Tizimda ishlatiladigan asosiy domain eventlar (hujjat sifatida):
EVENT_PAYMENT_SUCCEEDED = "payment_succeeded"
EVENT_PAYMENT_REFUNDED = "payment_refunded"
EVENT_ENROLLMENT_CREATED = "enrollment_created"
EVENT_LESSON_COMPLETED = "lesson_completed"
EVENT_COURSE_COMPLETED = "course_completed"
EVENT_CERTIFICATE_ISSUED = "certificate_issued"
EVENT_ASSIGNMENT_GRADED = "assignment_graded"
EVENT_USER_REGISTERED = "user_registered"
