from apps.assessments.models import Attempt, AttemptStatus


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
