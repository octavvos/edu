from apps.assessments.models import Attempt, AttemptStatus, Quiz
from apps.core.models import resolve_i18n


def get_my_quizzes(user, lang: str = "uz") -> list[dict]:
    """O'quvchining o'z guruhiga mentor tanlab jo'natgan testlari (Testlarim) —
    kursga yozilgan bo'lishning o'zi yetarli emas, test aynan shu guruhga
    yuborilgan bo'lishi kerak (Homework'ning guruh bo'yicha ko'rinish patterni)."""
    from apps.groups.selectors import get_active_membership

    membership = get_active_membership(user)
    if not membership:
        return []

    quizzes = (
        Quiz.objects.filter(assignments__group=membership.group)
        .select_related("lesson__module__course")
        .prefetch_related("questions")
        .distinct()
        .order_by("lesson__module__order", "lesson__order")
    )

    results = []
    for quiz in quizzes:
        lesson = quiz.lesson
        attempts = list(Attempt.objects.filter(user=user, quiz=quiz).order_by("-started_at"))
        submitted = [a for a in attempts if a.status == AttemptStatus.SUBMITTED]
        best_score = max((a.score_percent for a in submitted if a.score_percent is not None), default=None)
        passed = any(a.passed for a in submitted)
        in_progress = next((a for a in attempts if a.status == AttemptStatus.IN_PROGRESS), None)

        results.append({
            "lesson_id": str(lesson.id),
            "title": resolve_i18n(lesson.title, lang),
            "module_title": resolve_i18n(lesson.module.title, lang),
            "course_title": resolve_i18n(lesson.module.course.title, lang),
            "question_count": quiz.questions.count(),
            "time_limit_seconds": quiz.time_limit_seconds,
            "max_attempts": quiz.max_attempts,
            "pass_percent": quiz.pass_percent,
            "attempt_count": len(attempts),
            "best_score": best_score,
            "passed": passed,
            "has_in_progress": in_progress is not None,
            "in_progress_attempt_id": str(in_progress.id) if in_progress else None,
        })
    return results


def get_best_attempt_score(*, enrollment, quiz_lesson_id) -> float | None:
    best = (
        Attempt.objects.filter(
            enrollment=enrollment, quiz__lesson_id=quiz_lesson_id, status=AttemptStatus.SUBMITTED,
        )
        .order_by("-score_percent")
        .first()
    )
    return best.score_percent if best else None


def get_attempt_count(*, user, quiz) -> int:
    return Attempt.objects.filter(user=user, quiz=quiz).count()


def get_latest_attempt(*, user, quiz):
    return Attempt.objects.filter(user=user, quiz=quiz).order_by("-started_at").first()
