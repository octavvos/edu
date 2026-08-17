import random
import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.assessments.models import Answer, Attempt, AttemptStatus, Quiz
from apps.assessments.selectors import get_attempt_count, get_latest_attempt
from apps.core.exceptions import DomainError


class AssessmentError(DomainError):
    pass


@transaction.atomic
def start_attempt(*, user, enrollment, quiz: Quiz) -> Attempt:
    if get_attempt_count(user=user, quiz=quiz) >= quiz.max_attempts:
        raise AssessmentError("Urinishlar soni tugadi", code="max_attempts_reached")

    latest = get_latest_attempt(user=user, quiz=quiz)
    if latest and quiz.retake_cooldown_hours and latest.submitted_at:
        earliest_retry = latest.submitted_at + timedelta(hours=quiz.retake_cooldown_hours)
        if timezone.now() < earliest_retry:
            raise AssessmentError("Qayta topshirish uchun hali vaqt bor", code="cooldown_active")

    all_ids = list(quiz.questions.values_list("id", flat=True))
    if quiz.randomize_questions:
        random.shuffle(all_ids)
    if quiz.questions_per_attempt:
        all_ids = all_ids[: quiz.questions_per_attempt]

    expires_at = None
    if quiz.time_limit_seconds:
        expires_at = timezone.now() + timedelta(seconds=quiz.time_limit_seconds)

    return Attempt.objects.create(
        quiz=quiz, user=user, enrollment=enrollment,
        question_ids=[str(qid) for qid in all_ids], expires_at=expires_at,
    )


def submit_answer(*, attempt: Attempt, question, selected_choice_ids: list | None = None,
                   text_answer: str = "") -> Answer:
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise AssessmentError("Urinish allaqachon yakunlangan", code="attempt_closed")
    if attempt.expires_at and timezone.now() > attempt.expires_at:
        finalize_attempt(attempt=attempt)  # T-03: taymer tugaganda avtomatik yuborish
        raise AssessmentError("Vaqt tugadi", code="time_expired")

    is_correct, points = _grade_answer(question, selected_choice_ids or [], text_answer)
    answer, _ = Answer.objects.update_or_create(
        attempt=attempt, question=question,
        defaults={
            "selected_choice_ids": selected_choice_ids or [], "text_answer": text_answer,
            "is_correct": is_correct, "points_awarded": points,
        },
    )
    return answer


def _grade_answer(question, selected_choice_ids: list, text_answer: str) -> tuple[bool, float]:
    from apps.assessments.models import QuestionType

    if question.type in (QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE):
        correct_ids = set(str(c) for c in question.choices.filter(is_correct=True).values_list("id", flat=True))
        selected = set(str(c) for c in selected_choice_ids)
        is_correct = selected == correct_ids
    elif question.type == QuestionType.SHORT_TEXT:
        pattern = question.correct_text_pattern
        if question.is_regex:
            is_correct = bool(re.fullmatch(pattern, text_answer.strip(), re.IGNORECASE))
        else:
            is_correct = text_answer.strip().lower() == pattern.strip().lower()
    else:
        is_correct = False
    return is_correct, (question.points if is_correct else 0)


@transaction.atomic
def finalize_attempt(*, attempt: Attempt) -> Attempt:
    """T-04/T-07: yakuniy ball hisoblanadi va sertifikat shartiga bog'lanadi."""
    if attempt.status != AttemptStatus.IN_PROGRESS:
        return attempt

    answers = attempt.answers.select_related("question")
    total_points = sum(a.question.points for a in Answer.objects.filter(attempt=attempt).select_related("question"))
    earned_points = sum(a.points_awarded for a in answers)
    score_percent = round((earned_points / total_points) * 100, 2) if total_points else 0

    attempt.status = AttemptStatus.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.score_percent = score_percent
    attempt.passed = score_percent >= attempt.quiz.pass_percent
    attempt.save(update_fields=["status", "submitted_at", "score_percent", "passed"])

    if attempt.passed:
        from apps.enrollment.services import update_progress

        update_progress(enrollment=attempt.enrollment, lesson=attempt.quiz.lesson, mark_completed=True)
    return attempt
