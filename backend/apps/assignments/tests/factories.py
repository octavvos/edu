import factory
from factory.django import DjangoModelFactory

from apps.assignments.models import Homework
from apps.courses.tests.factories import CourseFactory
from apps.courses.models import Lesson, LessonType, Module
from apps.groups.tests.factories import GroupFactory


class ModuleFactory(DjangoModelFactory):
    class Meta:
        model = Module

    course = factory.SubFactory(CourseFactory)
    title = factory.Dict({"uz": "Modul"})
    order = factory.Sequence(lambda n: n)


class LessonFactory(DjangoModelFactory):
    class Meta:
        model = Lesson

    module = factory.SubFactory(ModuleFactory)
    type = LessonType.HOMEWORK
    title = factory.Dict({"uz": "Uy vazifasi"})
    order = factory.Sequence(lambda n: n)


class HomeworkFactory(DjangoModelFactory):
    class Meta:
        model = Homework

    lesson = factory.SubFactory(LessonFactory)
    group = factory.SubFactory(GroupFactory)
    instructions = factory.Dict({"uz": "Vazifani bajaring"})
    max_score = 100
