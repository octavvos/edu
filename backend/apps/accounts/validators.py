import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

USERNAME_MIN_LENGTH = 4
PASSWORD_MIN_LENGTH = 4


@deconstructible
class UsernameValidator:
    """
    Username: kamida 4 belgi, faqat lotin harflari, raqamlar va . _ - belgilari.
    Migratsiyalarda seriyalanishi uchun @deconstructible.
    """

    regex = re.compile(r"^[a-zA-Z0-9._-]+$")

    def __call__(self, value):
        errors = []
        if len(value) < USERNAME_MIN_LENGTH:
            errors.append(f"Username kamida {USERNAME_MIN_LENGTH} ta belgidan iborat bo'lishi kerak.")
        if not self.regex.match(value or ""):
            errors.append("Username faqat lotin harflari, raqamlar va . _ - belgilaridan iborat bo'lishi mumkin.")
        if errors:
            raise ValidationError(errors)

    def __eq__(self, other):
        return isinstance(other, UsernameValidator)


class PasswordComplexityValidator:
    """
    Parol uchun yagona talab — kamida 4 belgi (mahsulot qarori: o'quvchilar
    uchun ro'yxatdan o'tishni soddalashtirish). Murakkablik (katta harf/raqam)
    talab qilinmaydi.
    """

    def __init__(self, min_length: int = PASSWORD_MIN_LENGTH):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password or "") < self.min_length:
            raise ValidationError(
                f"Parol kamida {self.min_length} ta belgidan iborat bo'lishi kerak.",
                code="password_too_short",
            )

    def get_help_text(self):
        return f"Parol kamida {self.min_length} ta belgidan iborat bo'lishi kerak."
