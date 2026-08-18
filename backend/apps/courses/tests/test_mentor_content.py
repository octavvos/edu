"""Mentor kontent boshqaruvi: egalik tekshiruvi va material yuklash."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.tests.factories import UserFactory
from apps.core.exceptions import DomainError
from apps.courses import services
from apps.courses.selectors import get_mentor_courses
from apps.courses.tests.factories import CourseFactory, LessonFactory
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def test_mentor_courses_are_derived_from_active_groups():
    mentor = UserFactory()
    course = CourseFactory()
    GroupFactory(mentor=mentor, course=course)

    assert list(get_mentor_courses(mentor)) == [course]


def test_mentor_without_groups_has_no_courses():
    mentor = UserFactory()
    CourseFactory()

    assert list(get_mentor_courses(mentor)) == []


def test_assert_mentor_owns_course_passes_for_own_course():
    mentor = UserFactory()
    course = CourseFactory()
    GroupFactory(mentor=mentor, course=course)

    services.assert_mentor_owns_course(mentor=mentor, course=course)  # raise bo'lmasligi kerak


def test_assert_mentor_owns_course_rejects_unrelated_course():
    mentor = UserFactory()
    course = CourseFactory()

    with pytest.raises(DomainError) as exc:
        services.assert_mentor_owns_course(mentor=mentor, course=course)
    assert exc.value.status_code == 403


def test_add_file_material_attaches_to_lesson():
    lesson = LessonFactory()
    upload = SimpleUploadedFile("dars.pdf", b"%PDF-1.4 fake content", content_type="application/pdf")

    asset = services.add_file_material(lesson=lesson, file=upload)

    lesson.refresh_from_db()
    assert lesson.file_asset_id == asset.id
    assert asset.original_filename == "dars.pdf"
    assert asset.mime_type == "application/pdf"
    assert asset.size_bytes > 0


def test_add_file_material_replaces_previous_one():
    lesson = LessonFactory()
    first = services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("v1.pdf", b"old"),
    )
    second = services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("v2.pdf", b"new"),
    )

    lesson.refresh_from_db()
    assert lesson.file_asset_id == second.id
    from apps.courses.models import FileAsset

    assert not FileAsset.objects.filter(id=first.id).exists()


def test_add_module_and_lesson_via_services():
    course = CourseFactory()
    module = services.add_module(course=course, title={"uz": "1-modul"})
    lesson = services.add_lesson(module=module, type="text", title={"uz": "1-dars"})

    assert module.course_id == course.id
    assert lesson.module_id == module.id
    assert lesson.order == 1
