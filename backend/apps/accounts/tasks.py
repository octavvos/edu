from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task
def anonymize_expired_deletion_requests():
    """
    U-06: 30 kun grace davridan o'tgan akkauntlarni anonimlashtiradi.
    Moliyaviy yozuvlar (Order/Payment/LedgerEntry) anonim holda saqlanadi —
    faqat User PII maydonlari tozalanadi, moliyaviy tarix o'chirilmaydi.
    Beat jadvali: kuniga 1 marta (TZ 5.8).
    """
    from apps.accounts.models import User, UserStatus

    cutoff = timezone.now() - timedelta(days=30)
    qs = User.objects.filter(deletion_requested_at__lte=cutoff, anonymized_at__isnull=True)
    count = 0
    for user in qs:
        user.full_name = "O'chirilgan foydalanuvchi"
        user.phone = None
        user.email = None
        user.avatar = None
        user.birth_date = None
        user.city = ""
        user.status = UserStatus.ANONYMIZED
        user.anonymized_at = timezone.now()
        user.is_active = False
        user.set_unusable_password()
        user.save()
        count += 1
    return f"{count} ta foydalanuvchi anonimlashtirildi"


@shared_task
def cleanup_expired_otp_codes():
    """5.8: eski OTP kodlarni tozalash."""
    from apps.accounts.models import OTPCode

    cutoff = timezone.now() - timedelta(days=1)
    deleted, _ = OTPCode.objects.filter(created_at__lt=cutoff).delete()
    return f"{deleted} ta eski OTP o'chirildi"
