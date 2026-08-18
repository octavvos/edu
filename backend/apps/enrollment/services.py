from django.db import transaction
from django.utils import timezone

from apps.core.events import (
    EVENT_COURSE_COMPLETED,
    EVENT_ENROLLMENT_CREATED,
    EVENT_LESSON_COMPLETED,
    publish,
)
from apps.core.exceptions import DomainError
from apps.enrollment.models import AccessType, Enrollment, EnrollmentStatus, Progress, ProgressStatus
from apps.enrollment.selectors import get_enrollment, get_progress_map, is_lesson_unlocked


class EnrollmentError(DomainError):
    pass


@transaction.atomic
def enroll_free(*, user, course) -> Enrollment:
    if course.price > 0:
        raise EnrollmentError("Bu kurs pullik", code="course_not_free")
    return _create_enrollment(user=user, course=course, access_type=AccessType.FREE)


@transaction.atomic
def enroll_from_payment(*, user, course, order_id: str) -> Enrollment:
    """
    D-07: payments.services to'lov muvaffaqiyatli bo'lganda EVENT_PAYMENT_SUCCEEDED
    chiqaradi, apps.enrollment.handlers shu funksiyani chaqiradi — payments moduli
    enrollment'ni to'g'ridan-to'g'ri import qilmaydi.
    """
    return _create_enrollment(user=user, course=course, access_type=AccessType.PURCHASED, order_id=order_id)


@transaction.atomic
def enroll_by_group_admission(*, user, course) -> Enrollment:
    """
    D-07: mentor o'quvchini guruhga qabul qilganda apps.groups
    EVENT_STUDENT_ADMITTED chiqaradi, apps.enrollment.handlers shuni ushlab
    kursga yozadi — groups moduli enrollment'ni to'g'ridan-to'g'ri chaqirmaydi.
    """
    return _create_enrollment(user=user, course=course, access_type=AccessType.ADMIN_GRANTED)


def _create_enrollment(*, user, course, access_type: str, order_id: str | None = None) -> Enrollment:
    existing = get_enrollment(user=user, course=course)
    if existing and existing.status == EnrollmentStatus.ACTIVE:
        return existing

    enrollment = Enrollment.objects.create(
        user=user, course=course, course_version=course.published_version, access_type=access_type,
    )
    course.__class__.objects.filter(id=course.id).update(enrollment_count=course.enrollment_count + 1)
    publish(EVENT_ENROLLMENT_CREATED, user_id=str(user.id), course_id=str(course.id),
            enrollment_id=str(enrollment.id), order_id=order_id)
    return enrollment


def assert_lesson_access(*, user, lesson) -> Enrollment:
    course = lesson.module.course
    enrollment = get_enrollment(user=user, course=course)
    if lesson.is_free_preview:
        return enrollment  # bepul sinov — enrollment shart emas (None bo'lishi mumkin)
    if not enrollment or not enrollment.is_active:
        raise EnrollmentError("Bu darsga kirish uchun kursga yozilishingiz kerak", code="not_enrolled", status_code=403)
    if not is_lesson_unlocked(enrollment=enrollment, lesson=lesson):
        raise EnrollmentError("Bu dars hali ochilmagan", code="lesson_locked", status_code=403)
    return enrollment


@transaction.atomic
def update_progress(*, enrollment: Enrollment, lesson, seconds_watched: int = 0,
                     last_position: int = 0, mark_completed: bool = False) -> Progress:
    progress, _ = Progress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    progress.seconds_watched = max(progress.seconds_watched, seconds_watched)
    progress.last_position = last_position
    if progress.status == ProgressStatus.NOT_STARTED:
        progress.status = ProgressStatus.IN_PROGRESS

    newly_completed = False
    if mark_completed and progress.status != ProgressStatus.COMPLETED:
        progress.status = ProgressStatus.COMPLETED
        progress.completed_at = timezone.now()
        newly_completed = True
    progress.save()

    if newly_completed:
        publish(EVENT_LESSON_COMPLETED, user_id=str(enrollment.user_id),
                enrollment_id=str(enrollment.id), lesson_id=str(lesson.id))
        _recalculate_course_progress(enrollment)
    return progress


def _recalculate_course_progress(enrollment: Enrollment) -> None:
    """G-02/G-03: Enrollment'da denormalizatsiya qilinadi."""
    from apps.courses.models import Lesson

    total = Lesson.objects.filter(module__course_id=enrollment.course_id, is_required=True).count()
    if total == 0:
        return
    progress_map = get_progress_map(enrollment)
    completed = sum(
        1 for lesson_id, p in progress_map.items() if p.status == ProgressStatus.COMPLETED
    )
    enrollment.completed_lessons_count = completed
    enrollment.progress_percent = round(completed / total * 100, 2)

    if completed >= total and not enrollment.completed_at:
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["completed_lessons_count", "progress_percent", "completed_at"])
        publish(EVENT_COURSE_COMPLETED, user_id=str(enrollment.user_id),
                enrollment_id=str(enrollment.id), course_id=str(enrollment.course_id))
    else:
        enrollment.save(update_fields=["completed_lessons_count", "progress_percent"])


def get_playback_token(*, enrollment: Enrollment | None, lesson) -> dict:
    """V-06: qisqa muddatli signed URL (TTL <= 15 daq) + watermark matni."""
    from django.conf import settings

    if not lesson.video_asset or lesson.video_asset.status != "ready":
        raise EnrollmentError("Video hali tayyor emas", code="video_not_ready")

    user_id = str(enrollment.user_id) if enrollment else "preview"
    return {
        "manifest_url": lesson.video_asset.manifest_url,
        "expires_in": settings.SIGNED_URL_TTL_SECONDS,
        "watermark_text": user_id,
    }


def recalculate_progress_after_structure_change(course) -> None:
    """G-03: kurs strukturasi o'zgarganda aktiv enrollment'lar progressi qayta hisoblanadi."""
    for enrollment in Enrollment.objects.filter(course=course, status=EnrollmentStatus.ACTIVE):
        _recalculate_course_progress(enrollment)
