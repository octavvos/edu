import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    phone = factory.Sequence(lambda n: f"+99890{n:07d}")
    full_name = factory.Faker("name")
    is_phone_verified = True


class TeacherFactory(UserFactory):
    full_name = factory.Faker("name")
