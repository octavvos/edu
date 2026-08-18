from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.audit.services import log_action
from apps.core.exceptions import DomainError
from apps.core.models import StatusChoices
from apps.courses.models import Course, FileAsset, Lesson, Module


class CourseError(DomainError):
    pass


def assert_mentor_owns_course(*, mentor, course: Course) -> None:
    """Mentor faqat o'zi biriktirilgan guruhning kursiga material qo'sha oladi."""
    from apps.courses.selectors import get_mentor_courses

    if mentor.is_superuser:
        return
    if not get_mentor_courses(mentor).filter(id=course.id).exists():
        raise CourseError("Bu kurs sizga biriktirilmagan", code="not_your_course", status_code=403)


def assert_can_manage_lesson(*, mentor, lesson: Lesson) -> None:
    assert_mentor_owns_course(mentor=mentor, course=lesson.module.course)


def create_course(*, author, title: dict, category=None, **extra) -> Course:
    base_slug = slugify(title.get("uz") or title.get("en") or "course")
    slug = base_slug
    i = 1
    while Course.objects.filter(slug=slug).exists():
        i += 1
        slug = f"{base_slug}-{i}"
    return Course.objects.create(author=author, title=title, slug=slug, category=category, **extra)


def add_module(*, course: Course, title: dict) -> Module:
    next_order = (course.modules.count()) + 1
    return Module.objects.create(course=course, title=title, order=next_order)


def add_lesson(*, module: Module, type: str, title: dict, **extra) -> Lesson:  # noqa: A002
    next_order = module.lessons.count() + 1
    return Lesson.objects.create(module=module, type=type, title=title, order=next_order, **extra)


def reorder_modules(*, course: Course, ordered_ids: list[str]) -> None:
    """C-01: drag-and-drop bilan modul tartibini o'zgartirish."""
    for index, module_id in enumerate(ordered_ids, start=1):
        Module.objects.filter(course=course, id=module_id).update(order=index)


def reorder_lessons(*, module: Module, ordered_ids: list[str]) -> None:
    for index, lesson_id in enumerate(ordered_ids, start=1):
        Lesson.objects.filter(module=module, id=lesson_id).update(order=index)


def add_file_material(*, lesson: Lesson, file, is_downloadable: bool = True) -> FileAsset:
    """
    Material yuklash — hujjat/slayd/qo'shimcha fayl. Haqiqiy S3/MinIO
    backend orqali saqlanadi (STORAGES["default"]), video kabi tashqi
    provayder (Bunny) kerak emas.
    """
    asset = FileAsset.objects.create(
        file=file,
        original_filename=getattr(file, "name", "") or "",
        mime_type=getattr(file, "content_type", "") or "",
        size_bytes=getattr(file, "size", 0) or 0,
        is_downloadable=is_downloadable,
    )
    old_asset = lesson.file_asset
    lesson.file_asset = asset
    lesson.save(update_fields=["file_asset", "updated_at"])
    if old_asset:
        old_asset.delete()  # eski materialni almashtirishda ortiqcha faylni qoldirmaymiz
    return asset


def submit_for_moderation(*, actor, course: Course) -> Course:
    """C-02: draft -> pending_moderation."""
    if course.author_id != actor.id and not actor.has_perm_scoped("course.manage_any"):
        raise CourseError("Faqat muallif yuborishi mumkin", code="forbidden", status_code=403)
    if not course.modules.exists():
        raise CourseError("Kursda kamida bitta modul bo'lishi kerak", code="empty_course")

    course.status = StatusChoices.PENDING_MODERATION
    course.save(update_fields=["status"])
    return course


@transaction.atomic
def moderate_course(*, actor, course: Course, approve: bool, reason: str = "") -> Course:
    """AD-02: tasdiqlash / rad etish sababi bilan."""
    before = {"status": course.status}
    if approve:
        publish_course(actor=actor, course=course)
    else:
        course.status = StatusChoices.REJECTED
        course.rejection_reason = reason
        course.save(update_fields=["status", "rejection_reason"])
    log_action(actor=actor, action="course.moderate", obj=course, before=before,
               after={"status": course.status, "reason": reason})
    return course


@transaction.atomic
def publish_course(*, actor, course: Course) -> Course:
    """C-03: nashr etilgan kursning versiyalanishi."""
    from apps.courses.models import CourseVersion

    snapshot = _build_snapshot(course)
    next_version_no = (course.versions.order_by("-version_no").values_list("version_no", flat=True).first() or 0) + 1
    version = CourseVersion.objects.create(
        course=course, version_no=next_version_no, snapshot=snapshot,
        created_by=actor, published_at=timezone.now(),
    )
    course.published_version = version
    course.status = StatusChoices.PUBLISHED
    course.published_at = course.published_at or timezone.now()
    course.duration_minutes = _calc_duration_minutes(course)
    course.save(update_fields=["published_version", "status", "published_at", "duration_minutes"])

    from apps.catalog.tasks import reindex_course

    reindex_course.delay(str(course.id))
    return course


def _build_snapshot(course: Course) -> dict:
    modules = []
    for module in course.modules.order_by("order").prefetch_related("lessons"):
        modules.append({
            "id": str(module.id), "title": module.title, "order": module.order,
            "lessons": [
                {
                    "id": str(lesson.id), "type": lesson.type, "title": lesson.title,
                    "order": lesson.order, "is_required": lesson.is_required,
                    "is_free_preview": lesson.is_free_preview,
                }
                for lesson in module.lessons.order_by("order")
            ],
        })
    return {"title": course.title, "modules": modules}


def _calc_duration_minutes(course: Course) -> int:
    total_seconds = 0
    for lesson in Lesson.objects.filter(module__course=course, type="video").select_related("video_asset"):
        if lesson.video_asset:
            total_seconds += lesson.video_asset.duration_seconds
    return total_seconds // 60


@transaction.atomic
def duplicate_course(*, actor, course: Course) -> Course:
    """C-04: kursdan nusxa olish."""
    new_course = create_course(
        author=course.author, title={**course.title, "uz": f"{course.title.get('uz', '')} (nusxa)"},
        category=course.category, description=course.description, requirements=course.requirements,
        outcomes=course.outcomes, price=course.price, currency=course.currency,
        level=course.level, language=course.language, issues_certificate=course.issues_certificate,
    )
    for module in course.modules.order_by("order"):
        new_module = add_module(course=new_course, title=module.title)
        new_module.order = module.order
        new_module.save(update_fields=["order"])
        for lesson in module.lessons.order_by("order"):
            add_lesson(
                module=new_module, type=lesson.type, title=lesson.title,
                text_content=lesson.text_content, is_required=lesson.is_required,
                is_free_preview=lesson.is_free_preview, unlock_rule=lesson.unlock_rule,
                video_asset=lesson.video_asset, file_asset=lesson.file_asset,
            )
    log_action(actor=actor, action="course.duplicate", obj=new_course, after={"source": str(course.id)})
    return new_course
