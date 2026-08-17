from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """Email+parol yoki telefon+parol bilan kirish (Django admin va API uchun)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("phone") or kwargs.get("email")
        if not identifier or not password:
            return None
        try:
            user = User.objects.get(Q(phone=identifier) | Q(email__iexact=identifier))
        except User.DoesNotExist:
            User().set_password(password)  # timing-attack oldini olish
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
