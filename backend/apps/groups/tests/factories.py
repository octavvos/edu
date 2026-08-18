import factory
from factory.django import DjangoModelFactory

from apps.courses.tests.factories import CourseFactory
from apps.groups.models import Group, GroupSchedule, Weekday


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    course = factory.SubFactory(CourseFactory)
    name = factory.Sequence(lambda n: f"Guruh {n}")
    code = factory.Sequence(lambda n: f"guruh-{n}")
    capacity = 25


class GroupScheduleFactory(DjangoModelFactory):
    class Meta:
        model = GroupSchedule

    group = factory.SubFactory(GroupFactory)
    weekday = Weekday.MONDAY
    start_time = "18:00"
    end_time = "20:00"
