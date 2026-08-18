from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class UsernameOrContactBackend(ModelBackend):
    """
    Asosiy kirish usuli — username+parol. Eski hisoblar uchun telefon/email
    bilan kirish ham qo'llab-quvvatlanadi (bir xil `identifier` maydoni).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("phone") or kwargs.get("email")
        if not identifier or not password:
            return None
        try:
            user = User.objects.get(
                Q(username__iexact=identifier) | Q(phone=identifier) | Q(email__iexact=identifier),
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            User().set_password(password)  # timing-attack oldini olish
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
