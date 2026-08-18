from datetime import timedelta

import pytest
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.accounts import services
from apps.accounts.models import OTPCode, OTPPurpose, User, UserStatus
from apps.accounts.services import AuthError
from apps.accounts.tests.factories import UserFactory
from apps.groups.models import JoinRequestStatus
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def test_verify_otp_success():
    OTPCode.objects.create(
        phone="+998901234567", code_hash=make_password("123456"),
        purpose=OTPPurpose.LOGIN, expires_at=timezone.now() + timedelta(seconds=120),
    )
    otp = services.verify_otp(phone="+998901234567", code="123456", purpose=OTPPurpose.LOGIN)
    assert otp.used_at is not None


def test_verify_otp_wrong_code_raises():
    OTPCode.objects.create(
        phone="+998901234567", code_hash=make_password("123456"),
        purpose=OTPPurpose.LOGIN, expires_at=timezone.now() + timedelta(seconds=120),
    )
    with pytest.raises(AuthError):
        services.verify_otp(phone="+998901234567", code="000000", purpose=OTPPurpose.LOGIN)


def test_verify_otp_expired_raises():
    OTPCode.objects.create(
        phone="+998901234567", code_hash=make_password("123456"),
        purpose=OTPPurpose.LOGIN, expires_at=timezone.now() - timedelta(seconds=1),
    )
    with pytest.raises(AuthError):
        services.verify_otp(phone="+998901234567", code="123456", purpose=OTPPurpose.LOGIN)


def test_login_with_phone_returns_tokens_for_existing_user():
    UserFactory(phone="+998907654321")
    OTPCode.objects.create(
        phone="+998907654321", code_hash=make_password("111111"),
        purpose=OTPPurpose.LOGIN, expires_at=timezone.now() + timedelta(seconds=120),
    )
    user, tokens = services.login_with_phone(phone="+998907654321", code="111111")
    assert user.is_phone_verified is True
    assert "access" in tokens and "refresh" in tokens


def test_login_with_phone_does_not_create_account():
    """
    OTP orqali yangi hisob ochilmasligi kerak — aks holda o'quvchi mentor
    tasdig'ini chetlab o'tib faol hisobga ega bo'lardi.
    """
    OTPCode.objects.create(
        phone="+998900000001", code_hash=make_password("222222"),
        purpose=OTPPurpose.LOGIN, expires_at=timezone.now() + timedelta(seconds=120),
    )
    with pytest.raises(AuthError) as exc:
        services.login_with_phone(phone="+998900000001", code="222222")
    assert exc.value.status_code == 404
    assert not User.objects.filter(phone="+998900000001").exists()


def test_failed_login_locks_account_after_five_attempts():
    user = UserFactory(username="lockme")
    user.set_password("Sup3rSecret!")
    user.save()

    for _ in range(5):
        with pytest.raises(AuthError):
            services.login_with_password(identifier="lockme", password="wrong-pass")

    user.refresh_from_db()
    assert user.is_locked is True


# ---------------------------------------------------------------------------
# O'quvchining ro'yxatdan o'tishi
# ---------------------------------------------------------------------------

def test_register_student_creates_pending_account_and_join_request():
    group = GroupFactory(mentor=UserFactory())

    user, join_request = services.register_student(
        username="jasur", password="1234", first_name="Jasur",
        last_name="Toshmatov", group=group,
    )

    assert user.status == UserStatus.PENDING
    assert user.is_pending_approval is True
    assert user.display_name == "Jasur Toshmatov"
    assert join_request.status == JoinRequestStatus.PENDING
    assert join_request.group_id == group.id


def test_register_student_can_log_in_immediately():
    """Tasdiq kutayotgan o'quvchi ham "kutilmoqda" ekranini ko'rish uchun kira olishi kerak."""
    group = GroupFactory(mentor=UserFactory())
    services.register_student(
        username="kutuvchi", password="1234", first_name="Ali", last_name="Valiyev", group=group,
    )

    user, tokens = services.login_with_password(identifier="kutuvchi", password="1234")
    assert user.is_pending_approval is True
    assert "access" in tokens


def test_register_student_rejects_duplicate_username():
    group = GroupFactory(mentor=UserFactory())
    services.register_student(
        username="takror", password="1234", first_name="A", last_name="B", group=group,
    )

    with pytest.raises(AuthError) as exc:
        services.register_student(
            username="TAKROR", password="1234", first_name="C", last_name="D", group=group,
        )
    assert exc.value.code == "username_taken"


def test_register_student_rejects_short_password():
    group = GroupFactory(mentor=UserFactory())
    with pytest.raises(AuthError) as exc:
        services.register_student(
            username="qisqa", password="123", first_name="A", last_name="B", group=group,
        )
    assert exc.value.code == "weak_password"


def test_register_student_rejects_short_username():
    group = GroupFactory(mentor=UserFactory())
    with pytest.raises(AuthError) as exc:
        services.register_student(
            username="ab", password="1234", first_name="A", last_name="B", group=group,
        )
    assert exc.value.code == "invalid_username"


def test_four_character_password_is_accepted():
    group = GroupFactory(mentor=UserFactory())
    user, _ = services.register_student(
        username="mincheck", password="abcd", first_name="A", last_name="B", group=group,
    )
    assert user.check_password("abcd")
