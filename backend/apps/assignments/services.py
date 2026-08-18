from django.db import transaction
from django.utils import timezone

from apps.assignments.models import Grade, Homework, Submission, SubmissionStatus
from apps.core.events import EVENT_ASSIGNMENT_GRADED, publish
from apps.core.exceptions import DomainError


class AssignmentError(DomainError):
    pass


def _resolve_mentor_for(student):
    """
    H-02: topshiriqni tekshiradigan mentor — o'quvchi a'zo bo'lgan guruhning
    mentori. (Avval kurs-scoped RoleAssignment orqali "eng kam yuklangan
    mentor" tanlanardi; endi mentor guruhga biriktiriladi, shuning uchun
    taqsimlash guruh orqali aniq belgilanadi.)
    """
    from apps.groups.selectors import get_active_membership

    membership = get_active_membership(student)
    return membership.group.mentor if membership else None


@transaction.atomic
def submit_homework(*, user, enrollment, homework: Homework, file=None, text: str = "", link: str = "") -> Submission:
    if not (file or text or link):
        raise AssignmentError("Fayl, matn yoki havoladan kamida bittasi kerak", code="empty_submission")

    is_late = bool(homework.deadline_at and timezone.now() > homework.deadline_at)  # H-05
    mentor = _resolve_mentor_for(user)

    submission, _ = Submission.objects.update_or_create(
        homework=homework, user=user,
        defaults={
            "enrollment": enrollment, "file": file, "text": text, "link": link,
            "status": SubmissionStatus.SUBMITTED, "is_late": is_late, "mentor": mentor,
        },
    )
    return submission


@transaction.atomic
def send_homework(*, mentor, lesson, group, instructions: dict, deadline_at=None, max_score: int = 100,
                   material=None, presentation=None) -> Homework:
    """
    Mentor tanlangan guruhga vazifa jo'natadi. Vazifa faqat shu guruh
    o'quvchilariga ko'rinadi (`selectors.get_my_assignments`) — bitta kursni
    bir necha guruh baham ko'rgani uchun bu muhim. `material` (vazifa fayli)
    va `presentation` (taqdimot) bir-biridan mustaqil — ikkalasi ham
    tanlansa, ikkalasi ham o'quvchiga birga boradi.
    """
    from apps.courses.services import assert_can_manage_lesson

    assert_can_manage_lesson(mentor=mentor, lesson=lesson)

    if group.mentor_id != mentor.id and not mentor.is_superuser:
        raise AssignmentError("Bu guruh sizga biriktirilmagan", code="not_your_group", status_code=403)
    if group.course_id != lesson.module.course_id:
        raise AssignmentError("Guruh bu kursga tegishli emas", code="group_course_mismatch")
    if material is not None and material.lesson_id != lesson.id:
        raise AssignmentError("Material shu darsga tegishli emas", code="material_mismatch")
    if presentation is not None and presentation.lesson_id != lesson.id:
        raise AssignmentError("Taqdimot shu darsga tegishli emas", code="presentation_mismatch")

    homework, _ = Homework.objects.update_or_create(
        lesson=lesson, group=group,
        defaults={
            "instructions": instructions, "deadline_at": deadline_at,
            "max_score": max_score, "material": material, "presentation": presentation,
        },
    )
    return homework


def assign_mentor(*, submission: Submission, mentor) -> Submission:
    """H-02: qo'lda biriktirish (mentor bo'sh bo'lsa admin tomonidan)."""
    submission.mentor = mentor
    submission.status = SubmissionStatus.UNDER_REVIEW
    submission.save(update_fields=["mentor", "status"])
    return submission


# H-03: ruxsat etilgan holat o'tishlari.
# qabul qilindi — yakuniy holat, undan qaytish yo'q.
ALLOWED_TRANSITIONS = {
    SubmissionStatus.SUBMITTED: {SubmissionStatus.UNDER_REVIEW, SubmissionStatus.NEEDS_REVISION,
                                 SubmissionStatus.ACCEPTED},
    SubmissionStatus.UNDER_REVIEW: {SubmissionStatus.NEEDS_REVISION, SubmissionStatus.ACCEPTED},
    SubmissionStatus.NEEDS_REVISION: {SubmissionStatus.SUBMITTED, SubmissionStatus.UNDER_REVIEW},
    SubmissionStatus.ACCEPTED: set(),
}


def assert_can_review(*, mentor, submission: Submission) -> None:
    """
    Faqat topshiriq biriktirilgan mentor (yoki o'quvchi guruhining mentori)
    tekshira oladi. Global `assignment.grade` huquqiga ega rol ham o'tadi.
    """
    if submission.mentor_id == mentor.id:
        return
    if mentor.is_superuser:
        return

    from apps.groups.selectors import get_active_membership

    membership = get_active_membership(submission.user)
    if membership and membership.group.mentor_id == mentor.id:
        return

    raise AssignmentError(
        "Bu topshiriq sizga biriktirilmagan", code="not_your_submission", status_code=403,
    )


@transaction.atomic
def change_submission_status(*, mentor, submission: Submission, new_status: str) -> Submission:
    """H-03: holatni qo'lda o'zgartirish (masalan tekshirishni boshlash)."""
    assert_can_review(mentor=mentor, submission=submission)

    if new_status == submission.status:
        return submission
    if new_status not in ALLOWED_TRANSITIONS.get(submission.status, set()):
        raise AssignmentError(
            f"'{submission.get_status_display()}' holatidan bu holatga o'tib bo'lmaydi",
            code="invalid_transition",
        )

    # "Qabul qilindi" holatiga faqat baho qo'yish orqali o'tiladi — shunda
    # ball va izohsiz tasdiqlab yuborish imkoni bo'lmaydi.
    if new_status == SubmissionStatus.ACCEPTED:
        raise AssignmentError(
            "Qabul qilish uchun baho qo'ying", code="grade_required",
        )

    submission.status = new_status
    if submission.mentor_id is None:
        submission.mentor = mentor
    submission.save(update_fields=["status", "mentor", "updated_at"])
    return submission


@transaction.atomic
def grade_submission(*, mentor, submission: Submission, score: int, feedback: str = "",
                      needs_revision: bool = False) -> Submission:
    """H-04: mentor izohi va ball (0-100) qo'yishi."""
    assert_can_review(mentor=mentor, submission=submission)

    if not (0 <= score <= 100):
        raise AssignmentError("Ball 0 dan 100 gacha bo'lishi kerak", code="invalid_score")
    if submission.status == SubmissionStatus.ACCEPTED:
        raise AssignmentError("Bu topshiriq allaqachon qabul qilingan", code="already_accepted")

    Grade.objects.update_or_create(
        submission=submission, defaults={"mentor": mentor, "score": score, "feedback": feedback},
    )
    submission.status = SubmissionStatus.NEEDS_REVISION if needs_revision else SubmissionStatus.ACCEPTED
    if submission.mentor_id is None:
        submission.mentor = mentor
    submission.save(update_fields=["status", "mentor", "updated_at"])

    publish(EVENT_ASSIGNMENT_GRADED, user_id=str(submission.user_id), submission_id=str(submission.id))

    if submission.status == SubmissionStatus.ACCEPTED:
        from apps.enrollment.services import update_progress

        update_progress(enrollment=submission.enrollment, lesson=submission.homework.lesson, mark_completed=True)
    return submission
