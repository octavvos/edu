from django.utils import timezone

from apps.accounts.models import OTPCode, User, UserSession


def find_user_by_identifier(identifier: str) -> User | None:
    """Username birinchi navbatda — asosiy kirish usuli; telefon/email zaxira."""
    return (
        User.objects.filter(username__iexact=identifier).first()
        or User.objects.filter(phone=identifier).first()
        or User.objects.filter(email__iexact=identifier).first()
    )


def get_latest_otp(phone: str, purpose: str) -> OTPCode | None:
    return (
        OTPCode.objects.filter(phone=phone, purpose=purpose)
        .order_by("-created_at")
        .first()
    )


def count_recent_otp_requests(phone: str, since) -> int:
    return OTPCode.objects.filter(phone=phone, created_at__gte=since).count()


def get_active_sessions(user: User):
    return UserSession.objects.filter(user=user, revoked_at__isnull=True).select_related("device")


def get_active_device_count(user: User) -> int:
    return user.devices.filter(is_active=True).count()


def is_locked_out(user: User) -> bool:
    return bool(user.locked_until and user.locked_until > timezone.now())
