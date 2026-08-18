import factory
from factory.django import DjangoModelFactory

from apps.assessments.models import Quiz
from apps.courses.tests.factories import LessonFactory


class QuizFactory(DjangoModelFactory):
    class Meta:
        model = Quiz

    lesson = factory.SubFactory(LessonFactory)
    pass_percent = 60
    max_attempts = 1
