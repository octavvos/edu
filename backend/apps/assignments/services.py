from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.assignments.models import Grade, Homework, Submission, SubmissionStatus
from apps.core.events import EVENT_ASSIGNMENT_GRADED, publish
from apps.core.exceptions import DomainError


class AssignmentError(DomainError):
    pass


def _pick_mentor_round_robin(course):
    """H-02: mentorga avtomatik taqsimlash — kam yuklangan mentor tanlanadi."""
    from apps.rbac.models import RoleAssignment, ScopeType

    mentor_ids = RoleAssignment.objects.filter(
        role__codename="mentor", scope_type=ScopeType.COURSE, scope_id=course.id,
    ).values_list("user_id", flat=True)
    if not mentor_ids:
        return None

    load = (
        Submission.objects.filter(mentor_id__in=mentor_ids)
        .exclude(status=SubmissionStatus.ACCEPTED)
        .values("mentor_id")
        .annotate(count=Count("id"))
    )
    load_map = {row["mentor_id"]: row["count"] for row in load}
    return min(mentor_ids, key=lambda mid: load_map.get(mid, 0))


@transaction.atomic
def submit_homework(*, user, enrollment, homework: Homework, file=None, text: str = "", link: str = "") -> Submission:
    if not (file or text or link):
        raise AssignmentError("Fayl, matn yoki havoladan kamida bittasi kerak", code="empty_submission")

    is_late = bool(homework.deadline_at and timezone.now() > homework.deadline_at)  # H-05
    mentor_id = _pick_mentor_round_robin(homework.lesson.module.course)

    submission, _ = Submission.objects.update_or_create(
        homework=homework, user=user,
        defaults={
            "enrollment": enrollment, "file": file, "text": text, "link": link,
            "status": SubmissionStatus.SUBMITTED, "is_late": is_late, "mentor_id": mentor_id,
        },
    )
    return submission


def assign_mentor(*, submission: Submission, mentor) -> Submission:
    """H-02: qo'lda biriktirish (mentor bo'sh bo'lsa admin tomonidan)."""
    submission.mentor = mentor
    submission.status = SubmissionStatus.UNDER_REVIEW
    submission.save(update_fields=["mentor", "status"])
    return submission


@transaction.atomic
def grade_submission(*, mentor, submission: Submission, score: int, feedback: str = "",
                      needs_revision: bool = False) -> Submission:
    """H-04: mentor izohi va ball (0-100) qo'yishi."""
    if not (0 <= score <= 100):
        raise AssignmentError("Ball 0 dan 100 gacha bo'lishi kerak", code="invalid_score")

    Grade.objects.update_or_create(
        submission=submission, defaults={"mentor": mentor, "score": score, "feedback": feedback},
    )
    submission.status = SubmissionStatus.NEEDS_REVISION if needs_revision else SubmissionStatus.ACCEPTED
    submission.save(update_fields=["status"])

    publish(EVENT_ASSIGNMENT_GRADED, user_id=str(submission.user_id), submission_id=str(submission.id))

    if submission.status == SubmissionStatus.ACCEPTED:
        from apps.enrollment.services import update_progress

        update_progress(enrollment=submission.enrollment, lesson=submission.homework.lesson, mark_completed=True)
    return submission
