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

    assert list(lesson.materials.values_list("id", flat=True)) == [asset.id]
    assert asset.original_filename == "dars.pdf"
    assert asset.mime_type == "application/pdf"
    assert asset.size_bytes > 0


def test_add_file_material_keeps_multiple_files():
    """Bitta darsga bir nechta material qo'shilishi mumkin — avvalgisi o'chirilmaydi."""
    lesson = LessonFactory()
    first = services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("v1.pdf", b"old"),
    )
    second = services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("v2.pdf", b"new"),
    )

    from apps.courses.models import FileAsset

    assert set(lesson.materials.values_list("id", flat=True)) == {first.id, second.id}
    assert FileAsset.objects.filter(id=first.id).exists()


def test_remove_file_material_by_owning_mentor():
    mentor = UserFactory()
    course = CourseFactory()
    GroupFactory(mentor=mentor, course=course)
    lesson = LessonFactory(module__course=course)
    material = services.add_file_material(lesson=lesson, file=SimpleUploadedFile("a.pdf", b"x"))

    services.remove_file_material(mentor=mentor, material=material)

    from apps.courses.models import FileAsset

    assert not FileAsset.objects.filter(id=material.id).exists()


def test_remove_file_material_rejected_for_unrelated_mentor():
    lesson = LessonFactory()
    material = services.add_file_material(lesson=lesson, file=SimpleUploadedFile("a.pdf", b"x"))
    outsider = UserFactory()

    with pytest.raises(DomainError) as exc:
        services.remove_file_material(mentor=outsider, material=material)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Material yuklash validatsiyasi (kengaytma / hajm)
# ---------------------------------------------------------------------------

def test_material_upload_rejects_disallowed_extension():
    from apps.courses.api.mentor_serializers import MaterialUploadSerializer

    upload = SimpleUploadedFile("virus.exe", b"MZ...", content_type="application/octet-stream")
    serializer = MaterialUploadSerializer(data={"file": upload})

    assert not serializer.is_valid()
    assert "file" in serializer.errors


def test_material_upload_accepts_allowed_extension():
    from apps.courses.api.mentor_serializers import MaterialUploadSerializer

    upload = SimpleUploadedFile("dars.pdf", b"%PDF-1.4", content_type="application/pdf")
    serializer = MaterialUploadSerializer(data={"file": upload, "title": "Dars slaydlari", "kind": "presentation"})

    assert serializer.is_valid(), serializer.errors


def test_material_upload_rejects_oversized_file():
    from apps.courses.api.mentor_serializers import MaterialUploadSerializer
    from apps.courses.constants import MAX_MATERIAL_SIZE_BYTES

    oversized = SimpleUploadedFile("big.pdf", b"x" * (MAX_MATERIAL_SIZE_BYTES + 1))
    serializer = MaterialUploadSerializer(data={"file": oversized})

    assert not serializer.is_valid()
    assert "file" in serializer.errors


def test_material_upload_rejects_missing_kind():
    from apps.courses.api.mentor_serializers import MaterialUploadSerializer

    upload = SimpleUploadedFile("dars.pdf", b"%PDF-1.4", content_type="application/pdf")
    serializer = MaterialUploadSerializer(data={"file": upload, "title": "Dars slaydlari"})

    assert not serializer.is_valid()
    assert "kind" in serializer.errors


def test_material_upload_rejects_invalid_kind():
    from apps.courses.api.mentor_serializers import MaterialUploadSerializer

    upload = SimpleUploadedFile("dars.pdf", b"%PDF-1.4", content_type="application/pdf")
    serializer = MaterialUploadSerializer(
        data={"file": upload, "title": "Dars slaydlari", "kind": "not-a-real-kind"},
    )

    assert not serializer.is_valid()
    assert "kind" in serializer.errors


def test_add_module_and_lesson_via_services():
    course = CourseFactory()
    module = services.add_module(course=course, title={"uz": "1-modul"})
    lesson = services.add_lesson(module=module, type="text", title={"uz": "1-dars"})

    assert module.course_id == course.id
    assert lesson.module_id == module.id
    assert lesson.order == 1
