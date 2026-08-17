from datetime import timedelta

import pytest
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.accounts import services
from apps.accounts.models import OTPCode, OTPPurpose
from apps.accounts.services import AuthError
from apps.accounts.tests.factories import UserFactory

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


def test_register_or_login_with_phone_creates_new_user():
    OTPCode.objects.create(
        phone="+998907654321", code_hash=make_password("111111"),
        purpose=OTPPurpose.LOGIN, expires_at=timezone.now() + timedelta(seconds=120),
    )
    user, tokens = services.register_or_login_with_phone(phone="+998907654321", code="111111")
    assert user.is_phone_verified is True
    assert "access" in tokens and "refresh" in tokens


def test_failed_login_locks_account_after_five_attempts():
    user = UserFactory(phone=None, email="lock@test.uz")
    user.set_password("Sup3rSecret!")
    user.save()

    for _ in range(5):
        with pytest.raises(AuthError):
            services.login_with_password(identifier="lock@test.uz", password="wrong-pass")

    user.refresh_from_db()
    assert user.is_locked is True
