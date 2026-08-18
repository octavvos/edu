import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User, UserStatus


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    # username — USERNAME_FIELD, unique bo'lgani uchun Sequence bilan beriladi
    username = factory.Sequence(lambda n: f"user{n:05d}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    full_name = factory.LazyAttribute(lambda o: f"{o.first_name} {o.last_name}")
    phone = factory.Sequence(lambda n: f"+99890{n:07d}")
    is_phone_verified = True
    status = UserStatus.ACTIVE


class PendingUserFactory(UserFactory):
    """Ro'yxatdan o'tgan, lekin mentor hali tasdiqlamagan o'quvchi."""

    status = UserStatus.PENDING


class TeacherFactory(UserFactory):
    username = factory.Sequence(lambda n: f"teacher{n:05d}")
