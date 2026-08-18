"""
Barcha yozish operatsiyalari shu yerda — API view'lar, admin va Celery
bir xil logikadan foydalanadi (TZ 5.1 qoidasi).
"""

import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import (
    Device,
    LoginAttempt,
    OTPCode,
    OTPPurpose,
    User,
    UserSession,
    UserStatus,
)
from apps.accounts.selectors import (
    count_recent_otp_requests,
    find_user_by_identifier,
    get_active_device_count,
    get_latest_otp,
)
from apps.core.events import EVENT_USER_REGISTERED, publish
from apps.core.exceptions import DomainError


class AuthError(DomainError):
    pass


# ---------------------------------------------------------------------------
# OTP (A-04)
# ---------------------------------------------------------------------------

def request_otp(*, phone: str, purpose: str, ip_address: str | None = None) -> OTPCode:
    since = timezone.now() - timedelta(hours=1)
    if count_recent_otp_requests(phone, since) >= settings.OTP_MAX_PER_HOUR:
        raise AuthError("Bu raqamga soatiga ruxsat etilgan SMS soni tugadi", code="otp_rate_limited", status_code=429)

    code = f"{random.randint(0, 999999):06d}"
    otp = OTPCode.objects.create(
        phone=phone,
        code_hash=make_password(code),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(seconds=settings.OTP_TTL_SECONDS),
        ip_address=ip_address,
    )

    from apps.notifications.tasks import send_otp_sms

    send_otp_sms.delay(phone=phone, code=code)
    return otp


def verify_otp(*, phone: str, code: str, purpose: str) -> OTPCode:
    otp = get_latest_otp(phone, purpose)
    if not otp or not otp.is_valid:
        raise AuthError("OTP kod noto'g'ri yoki muddati tugagan", code="otp_invalid")

    otp.attempts += 1
    if not check_password(code, otp.code_hash):
        otp.save(update_fields=["attempts"])
        raise AuthError("OTP kod noto'g'ri", code="otp_invalid")

    otp.used_at = timezone.now()
    otp.save(update_fields=["attempts", "used_at"])
    return otp


# ---------------------------------------------------------------------------
# Ro'yxatdan o'tish / kirish
# ---------------------------------------------------------------------------

def login_with_phone(*, phone: str, code: str, device_id: str | None = None,
                     ip_address: str | None = None, user_agent: str = "") -> tuple[User, dict]:
    """
    Telefon+OTP orqali MAVJUD hisobga kirish (qulaylik uchun qo'shimcha usul).

    Bu yerda yangi hisob YARATILMAYDI: ro'yxatdan o'tishning yagona yo'li —
    `register_student()`, ya'ni guruh tanlab, mentor tasdig'ini kutish. Aks
    holda OTP orqali kimdir tasdiqsiz faol hisob ochib olishi mumkin edi.
    """
    verify_otp(phone=phone, code=code, purpose=OTPPurpose.LOGIN)

    user = User.objects.filter(phone=phone).first()
    if not user:
        raise AuthError(
            "Bu raqam bo'yicha hisob topilmadi. Avval ro'yxatdan o'ting.",
            code="user_not_found", status_code=404,
        )

    if not user.is_phone_verified:
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

    tokens = issue_tokens(user=user, device_id=device_id, ip_address=ip_address, user_agent=user_agent)
    return user, tokens


@transaction.atomic
def register_student(*, username: str, password: str, first_name: str, last_name: str,
                     group) -> tuple[User, "object"]:
    """
    O'quvchining ro'yxatdan o'tishi: hisob `pending` holatda ochiladi va
    tanlangan guruhga qo'shilish so'rovi yaratiladi. Mentor tasdiqlamaguncha
    o'quvchi hech qanday kursni ko'ra olmaydi.

    Guruh (`group`) chaqiruvchi tomonidan topib beriladi — accounts app
    groups app'iga bog'lanib qolmasligi uchun.
    """
    if User.objects.filter(username__iexact=username).exists():
        raise AuthError("Bu username allaqachon band", code="username_taken")

    _validate_username(username)
    _validate_password(password)

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        full_name=f"{first_name.strip()} {last_name.strip()}".strip(),
        status=UserStatus.PENDING,
    )

    from apps.groups.services import create_join_request
    from apps.rbac.services import assign_role_by_codename

    assign_role_by_codename(user=user, codename="student")
    join_request = create_join_request(student=user, group=group)

    publish(EVENT_USER_REGISTERED, user_id=str(user.id), channel="username")
    return user, join_request


def _validate_username(username: str) -> None:
    from apps.accounts.validators import UsernameValidator

    try:
        UsernameValidator()(username)
    except DjangoValidationError as exc:
        raise AuthError("; ".join(exc.messages), code="invalid_username") from exc


def _validate_password(password: str) -> None:
    from django.contrib.auth.password_validation import validate_password

    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise AuthError("; ".join(exc.messages), code="weak_password") from exc


def login_with_password(*, identifier: str, password: str, device_id: str | None = None,
                         ip_address: str | None = None, user_agent: str = "",
                         otp_code: str | None = None) -> tuple[User, dict]:
    user = find_user_by_identifier(identifier)

    if user and user.is_locked:
        _log_attempt(identifier, False, ip_address, user_agent, "locked")
        raise AuthError("Hisob vaqtincha bloklangan, keyinroq urinib ko'ring", code="account_locked", status_code=423)

    authenticated = authenticate(username=identifier, password=password)
    if authenticated is None:
        _register_failed_attempt(user)
        _log_attempt(identifier, False, ip_address, user_agent, "bad_credentials")
        raise AuthError("Login yoki parol noto'g'ri", code="invalid_credentials", status_code=401)

    if authenticated.status == UserStatus.BLOCKED:
        _log_attempt(identifier, False, ip_address, user_agent, "blocked")
        raise AuthError("Hisob bloklangan", code="account_blocked", status_code=403)

    # A-06: admin/super-admin uchun 2FA majburiy
    if authenticated.requires_2fa() and authenticated.totp_enabled:
        if not otp_code or not _verify_totp(authenticated, otp_code):
            raise AuthError("2FA kod talab qilinadi", code="2fa_required", status_code=401)

    authenticated.failed_login_attempts = 0
    authenticated.locked_until = None
    authenticated.save(update_fields=["failed_login_attempts", "locked_until"])
    _log_attempt(identifier, True, ip_address, user_agent, "")

    tokens = issue_tokens(user=authenticated, device_id=device_id, ip_address=ip_address, user_agent=user_agent)
    return authenticated, tokens


def _register_failed_attempt(user: User | None) -> None:
    if not user:
        return
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= 5:  # A-07
        user.locked_until = timezone.now() + timedelta(minutes=15)
    user.save(update_fields=["failed_login_attempts", "locked_until"])


def _verify_totp(user: User, token: str) -> bool:
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    return bool(device and device.verify_token(token))


def _log_attempt(identifier: str, success: bool, ip_address, user_agent, reason: str) -> None:
    LoginAttempt.objects.create(
        identifier=identifier, success=success, ip_address=ip_address,
        user_agent=user_agent[:255], reason=reason,
    )


# ---------------------------------------------------------------------------
# Token / sessiya (A-02, A-03, A-08, A-09)
# ---------------------------------------------------------------------------

def issue_tokens(*, user: User, device_id: str | None, ip_address: str | None, user_agent: str) -> dict:
    device = None
    if device_id:
        device, _ = Device.objects.update_or_create(
            user=user, device_id=device_id,
            defaults={"is_active": True, "name": user_agent[:255]},
        )
        _enforce_device_limit(user)

    refresh = RefreshToken.for_user(user)
    UserSession.objects.create(
        user=user, device=device, refresh_jti=str(refresh["jti"]),
        ip_address=ip_address, user_agent=user_agent[:255],
    )

    # Django `last_login`ni faqat contrib.auth.login() yangilaydi; biz JWT
    # ishlatamiz, shuning uchun qo'lda yozamiz — mentor o'quvchi faolligini
    # ("oxirgi kirgan vaqt") shu maydon orqali kuzatadi.
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _enforce_device_limit(user: User) -> None:
    limit = user.max_active_devices or settings.MAX_ACTIVE_DEVICES
    active = list(user.devices.filter(is_active=True).order_by("-last_seen_at"))
    if len(active) > limit:
        for stale in active[limit:]:
            stale.is_active = False
            stale.save(update_fields=["is_active"])
            UserSession.objects.filter(device=stale, revoked_at__isnull=True).update(revoked_at=timezone.now())


def revoke_session(*, session: UserSession) -> None:
    """A-08: sessiyani masofadan uzish."""
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])
    outstanding = OutstandingToken.objects.filter(jti=session.refresh_jti).first()
    if outstanding:
        BlacklistedToken.objects.get_or_create(token=outstanding)


def logout(*, user: User, refresh_jti: str) -> None:
    session = UserSession.objects.filter(user=user, refresh_jti=refresh_jti).first()
    if session:
        revoke_session(session=session)


def request_account_deletion(*, user: User) -> None:
    """U-06: 30 kun grace davri -> anonimizatsiya."""
    user.deletion_requested_at = timezone.now()
    user.save(update_fields=["deletion_requested_at"])
