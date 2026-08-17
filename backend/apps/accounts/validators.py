import re

from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    """A-01: parol minimal 8 belgi, katta/kichik harf va raqam."""

    def validate(self, password, user=None):
        errors = []
        if not re.search(r"[A-Z]", password):
            errors.append("Parolda kamida bitta katta harf bo'lishi kerak.")
        if not re.search(r"[a-z]", password):
            errors.append("Parolda kamida bitta kichik harf bo'lishi kerak.")
        if not re.search(r"\d", password):
            errors.append("Parolda kamida bitta raqam bo'lishi kerak.")
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "Parol katta harf, kichik harf va raqamdan iborat bo'lishi kerak."
