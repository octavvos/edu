import random
import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.assessments.models import Answer, Attempt, AttemptStatus, Choice, Question, QuestionType, Quiz
from apps.assessments.selectors import get_attempt_count, get_latest_attempt
from apps.core.exceptions import DomainError


class AssessmentError(DomainError):
    pass


# ---------------------------------------------------------------------------
# Mentor: test yaratish/tahrirlash (T01-T07)
# ---------------------------------------------------------------------------

CHOICE_BASED_TYPES = {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE}


def create_quiz(*, lesson, **fields) -> Quiz:
    if hasattr(lesson, "quiz"):
        raise AssessmentError("Bu darsda test allaqachon mavjud", code="quiz_exists")
    return Quiz.objects.create(lesson=lesson, **fields)


def update_quiz(*, quiz: Quiz, **fields) -> Quiz:
    for key, value in fields.items():
        setattr(quiz, key, value)
    quiz.save()
    return quiz


def _validate_choices(question_type: str, choices: list[dict]) -> None:
    if question_type not in CHOICE_BASED_TYPES:
        return
    if len(choices) < 2:
        raise AssessmentError("Kamida 2 ta variant kerak", code="not_enough_choices")

    correct_count = sum(1 for c in choices if c.get("is_correct"))
    if question_type in (QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE):
        if correct_count != 1:
            raise AssessmentError(
                "Bu turdagi savolda aynan bitta to'g'ri javob belgilanishi kerak",
                code="invalid_correct_count",
            )
    elif question_type == QuestionType.MULTIPLE_CHOICE and correct_count == 0:
        raise AssessmentError(
            "Kamida bitta to'g'ri javob belgilanishi kerak", code="invalid_correct_count",
        )


@transaction.atomic
def add_question(*, quiz: Quiz, type: str, text: dict, points: int = 1,  # noqa: A002
                 explanation: dict | None = None, correct_text_pattern: str = "",
                 is_regex: bool = False, choices: list[dict] | None = None) -> Question:
    choices = choices or []
    _validate_choices(type, choices)
    if type == QuestionType.SHORT_TEXT and not correct_text_pattern:
        raise AssessmentError("To'g'ri javob namunasi kiritilishi kerak", code="pattern_required")

    order = quiz.questions.count() + 1
    question = Question.objects.create(
        quiz=quiz, type=type, text=text, explanation=explanation or {}, points=points,
        order=order, correct_text_pattern=correct_text_pattern, is_regex=is_regex,
    )
    if choices:
        Choice.objects.bulk_create([
            Choice(question=question, text=c["text"], is_correct=bool(c.get("is_correct")), order=i)
            for i, c in enumerate(choices)
        ])
    return question


@transaction.atomic
def update_question(*, question: Question, choices: list[dict] | None = None, **fields) -> Question:
    question_type = fields.get("type", question.type)
    if choices is not None:
        _validate_choices(question_type, choices)
    if fields.get("type") == QuestionType.SHORT_TEXT and not fields.get(
        "correct_text_pattern", question.correct_text_pattern,
    ):
        raise AssessmentError("To'g'ri javob namunasi kiritilishi kerak", code="pattern_required")

    for key, value in fields.items():
        setattr(question, key, value)
    question.save()

    if choices is not None:
        question.choices.all().delete()
        Choice.objects.bulk_create([
            Choice(question=question, text=c["text"], is_correct=bool(c.get("is_correct")), order=i)
            for i, c in enumerate(choices)
        ])
    return question


def delete_question(*, question: Question) -> None:
    question.delete()


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
