import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_otp_sms(self, phone: str, code: str):
    """A-04: OTP SMS. N-02: SMS faqat OTP va kritik to'lov hodisalari uchun."""
    from apps.notifications.backends.sms import get_sms_backend

    message = f"Onlayn ta'lim: tasdiqlash kodi — {code}. Kodni hech kimga aytmang."
    ok = get_sms_backend().send(phone, message)
    if not ok:
        raise self.retry(exc=RuntimeError("SMS yuborilmadi"))
    return True


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_verification(self, user_id: str):
    from apps.accounts.models import User
    from apps.notifications.tokens import generate_email_verification_token

    user = User.objects.get(id=user_id)
    token = generate_email_verification_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/verify-email?token={token}"
    _send_email_safe(
        self, to=user.email, subject="Emailni tasdiqlang",
        body=f"Emailingizni tasdiqlash uchun havola: {link}",
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_link(self, user_id: str):
    from apps.accounts.models import User
    from apps.notifications.tokens import generate_password_reset_token

    user = User.objects.get(id=user_id)
    token = generate_password_reset_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}"
    if user.email:
        _send_email_safe(
            self, to=user.email, subject="Parolni tiklash",
            body=f"Parolni tiklash uchun havola (15 daqiqa amal qiladi): {link}",
        )
    elif user.phone:
        from apps.notifications.backends.sms import get_sms_backend

        get_sms_backend().send(user.phone, f"Parolni tiklash havolasi: {link}")


def _send_email_safe(task, *, to: str, subject: str, body: str):
    try:
        send_mail(subject, body, None, [to], fail_silently=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Email yuborishda xatolik: to=%s", to)
        raise task.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def dispatch_notification(self, *, user_id: str, event: str, context: dict | None = None,
                           channels: list[str] | None = None):
    """
    N-01..N-05: umumiy bildirishnoma dispatcheri — shablon + foydalanuvchi
    sozlamasi asosida in-app/push/email yuboradi.
    """
    from apps.accounts.models import User
    from apps.notifications.models import (
        DispatchStatus,
        NotificationDispatch,
        NotificationPreference,
        NotificationTemplate,
    )

    user = User.objects.filter(id=user_id).first()
    if not user:
        return

    templates = NotificationTemplate.objects.filter(event=event, is_active=True)
    if channels:
        templates = templates.filter(channel__in=channels)

    for template in templates:
        enabled = NotificationPreference.objects.filter(
            user=user, event=event, channel=template.channel,
        ).values_list("enabled", flat=True).first()
        if enabled is False:
            continue

        dispatch = NotificationDispatch.objects.create(
            user=user, event=event, channel=template.channel, payload=context or {},
        )
        try:
            _deliver(user=user, template=template, context=context or {})
            dispatch.status = DispatchStatus.SENT
            dispatch.sent_at = timezone.now()
        except Exception as exc:  # noqa: BLE001
            dispatch.status = DispatchStatus.FAILED
            dispatch.error = str(exc)[:1000]
            dispatch.attempts += 1
            logger.exception("Notification dispatch failed: event=%s user=%s", event, user_id)
        dispatch.save()


def _deliver(*, user, template, context: dict) -> None:
    from apps.core.models import get_i18n_value

    body = get_i18n_value(template, "body", user.language).format(**context)
    if template.channel == "email" and user.email:
        send_mail(get_i18n_value(template, "subject", user.language) or "Bildirishnoma", body, None, [user.email])
    elif template.channel == "sms" and user.phone:
        from apps.notifications.backends.sms import get_sms_backend

        get_sms_backend().send(user.phone, body)
    # in_app / push — NotificationDispatch yozuvining o'zi in-app feed manbai;
    # push uchun FCM integratsiyasi libs/fcm orqali kelajakda qo'shiladi.
