import pytest

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory, LessonFactory, ModuleFactory
from apps.enrollment import services

pytestmark = pytest.mark.django_db


def test_enroll_free_creates_enrollment_and_increments_count():
    user = UserFactory()
    course = CourseFactory(price=0)

    enrollment = services.enroll_free(user=user, course=course)
    course.refresh_from_db()

    assert enrollment.user_id == user.id
    assert course.enrollment_count == 1


def test_enroll_free_rejects_paid_course():
    user = UserFactory()
    course = CourseFactory(price=100000)

    with pytest.raises(services.EnrollmentError):
        services.enroll_free(user=user, course=course)


def test_update_progress_completes_course_when_all_required_lessons_done():
    user = UserFactory()
    course = CourseFactory(price=0)
    module = ModuleFactory(course=course)
    lesson1 = LessonFactory(module=module, order=1)
    lesson2 = LessonFactory(module=module, order=2)

    enrollment = services.enroll_free(user=user, course=course)

    services.update_progress(enrollment=enrollment, lesson=lesson1, mark_completed=True)
    enrollment.refresh_from_db()
    assert enrollment.progress_percent == 50.0
    assert enrollment.completed_at is None

    services.update_progress(enrollment=enrollment, lesson=lesson2, mark_completed=True)
    enrollment.refresh_from_db()
    assert enrollment.progress_percent == 100.0
    assert enrollment.completed_at is not None


def test_assert_lesson_access_denied_without_enrollment():
    user = UserFactory()
    course = CourseFactory(price=0)
    module = ModuleFactory(course=course)
    lesson = LessonFactory(module=module, is_free_preview=False)

    with pytest.raises(services.EnrollmentError):
        services.assert_lesson_access(user=user, lesson=lesson)


def test_assert_lesson_access_allowed_for_free_preview():
    user = UserFactory()
    course = CourseFactory(price=0)
    module = ModuleFactory(course=course)
    lesson = LessonFactory(module=module, is_free_preview=True)

    # Enrollment bo'lmasa ham xatolik ko'tarilmasligi kerak
    services.assert_lesson_access(user=user, lesson=lesson)
