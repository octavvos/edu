import pytest

from apps.accounts.tests.factories import TeacherFactory
from apps.core.models import StatusChoices
from apps.courses import services
from apps.courses.tests.factories import CourseFactory, LessonFactory, ModuleFactory

pytestmark = pytest.mark.django_db


def test_submit_for_moderation_requires_at_least_one_module():
    teacher = TeacherFactory()
    course = CourseFactory(author=teacher)
    with pytest.raises(services.CourseError):
        services.submit_for_moderation(actor=teacher, course=course)


def test_publish_course_creates_version_and_sets_published():
    teacher = TeacherFactory()
    course = CourseFactory(author=teacher)
    module = ModuleFactory(course=course)
    LessonFactory(module=module)

    services.publish_course(actor=teacher, course=course)
    course.refresh_from_db()

    assert course.status == StatusChoices.PUBLISHED
    assert course.published_version is not None
    assert course.versions.count() == 1


def test_reorder_modules_updates_order():
    course = CourseFactory()
    m1 = ModuleFactory(course=course, order=1)
    m2 = ModuleFactory(course=course, order=2)

    services.reorder_modules(course=course, ordered_ids=[str(m2.id), str(m1.id)])
    m1.refresh_from_db()
    m2.refresh_from_db()

    assert m2.order == 1
    assert m1.order == 2


def test_duplicate_course_copies_structure():
    teacher = TeacherFactory()
    course = CourseFactory(author=teacher)
    module = ModuleFactory(course=course)
    LessonFactory(module=module)

    duplicate = services.duplicate_course(actor=teacher, course=course)

    assert duplicate.id != course.id
    assert duplicate.modules.count() == 1
    assert duplicate.modules.first().lessons.count() == 1
