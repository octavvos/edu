import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import TeacherFactory
from apps.courses.models import Course, Lesson, LessonType, Module


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    author = factory.SubFactory(TeacherFactory)
    slug = factory.Sequence(lambda n: f"test-course-{n}")
    title = factory.LazyAttribute(lambda o: {"uz": f"Test kurs {o.slug}"})
    price = 0


class ModuleFactory(DjangoModelFactory):
    class Meta:
        model = Module

    course = factory.SubFactory(CourseFactory)
    title = factory.LazyAttribute(lambda o: {"uz": "Modul 1"})
    order = 1


class LessonFactory(DjangoModelFactory):
    class Meta:
        model = Lesson

    module = factory.SubFactory(ModuleFactory)
    type = LessonType.TEXT
    title = factory.LazyAttribute(lambda o: {"uz": "Dars 1"})
    order = 1
