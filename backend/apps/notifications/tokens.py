"""
Statsiz (stateless), imzolangan tokenlar — email tasdiqlash va parolni
tiklash uchun (A-05: havola 15 daqiqa amal qiladi).
"""

from django.core import signing
from django.core.signing import BadSignature, SignatureExpired

EMAIL_VERIFY_SALT = "accounts.email_verification"
PASSWORD_RESET_SALT = "accounts.password_reset"
PASSWORD_RESET_MAX_AGE = 15 * 60  # A-05: 15 daqiqa
EMAIL_VERIFY_MAX_AGE = 24 * 60 * 60


def generate_email_verification_token(user) -> str:
    return signing.dumps({"user_id": str(user.id)}, salt=EMAIL_VERIFY_SALT)


def verify_email_verification_token(token: str):
    from apps.accounts.models import User
    from apps.accounts.services import AuthError

    try:
        data = signing.loads(token, salt=EMAIL_VERIFY_SALT, max_age=EMAIL_VERIFY_MAX_AGE)
    except (BadSignature, SignatureExpired) as exc:
        raise AuthError("Havola yaroqsiz yoki muddati tugagan", code="invalid_token") from exc
    return User.objects.get(id=data["user_id"])


def generate_password_reset_token(user) -> str:
    return signing.dumps({"user_id": str(user.id)}, salt=PASSWORD_RESET_SALT)


def verify_password_reset_token(token: str):
    from apps.accounts.models import User
    from apps.accounts.services import AuthError

    try:
        data = signing.loads(token, salt=PASSWORD_RESET_SALT, max_age=PASSWORD_RESET_MAX_AGE)
    except (BadSignature, SignatureExpired) as exc:
        raise AuthError("Havola yaroqsiz yoki muddati tugagan", code="invalid_token") from exc
    try:
        return User.objects.get(id=data["user_id"])
    except User.DoesNotExist as exc:
        raise AuthError("Foydalanuvchi topilmadi", code="user_not_found") from exc
