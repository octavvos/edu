from apps.core.models import StatusChoices
from apps.courses.models import Course, Module


def get_published_course(*, slug: str) -> Course | None:
    return (
        Course.objects.filter(slug=slug, status=StatusChoices.PUBLISHED)
        .select_related("author", "category")
        .prefetch_related("modules__lessons")
        .first()
    )


def get_course_syllabus(course: Course):
    return Module.objects.filter(course=course).prefetch_related("lessons").order_by("order")


def get_teacher_courses(teacher):
    return Course.objects.filter(author=teacher).order_by("-created_at")


def get_moderation_queue():
    """AD-02: kurslar moderatsiyasi navbati."""
    return Course.objects.filter(status=StatusChoices.PENDING_MODERATION).select_related("author").order_by("created_at")


def get_free_preview_lessons(course: Course):
    from apps.courses.models import Lesson

    return Lesson.objects.filter(module__course=course, is_free_preview=True)
