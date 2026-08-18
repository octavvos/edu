"""Mentor test builder'i: quiz/savol/variant yaratish va tahrirlash."""

import pytest

from apps.assessments import services
from apps.assessments.models import QuestionType
from apps.assessments.tests.factories import QuizFactory
from apps.core.exceptions import DomainError
from apps.courses.tests.factories import LessonFactory

pytestmark = pytest.mark.django_db


def test_create_quiz_for_lesson():
    lesson = LessonFactory()
    quiz = services.create_quiz(lesson=lesson, pass_percent=70, max_attempts=2)

    assert quiz.lesson_id == lesson.id
    assert quiz.pass_percent == 70


def test_cannot_create_second_quiz_on_same_lesson():
    lesson = LessonFactory()
    services.create_quiz(lesson=lesson)

    with pytest.raises(DomainError) as exc:
        services.create_quiz(lesson=lesson)
    assert exc.value.code == "quiz_exists"


def test_update_quiz_settings():
    quiz = QuizFactory(pass_percent=60)
    updated = services.update_quiz(quiz=quiz, pass_percent=80, max_attempts=3)

    assert updated.pass_percent == 80
    assert updated.max_attempts == 3


# ---------------------------------------------------------------------------
# Savol qo'shish — turlar bo'yicha tekshiruv
# ---------------------------------------------------------------------------

def test_add_single_choice_question():
    quiz = QuizFactory()
    question = services.add_question(
        quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "2+2 nechchi?"},
        choices=[
            {"text": {"uz": "3"}, "is_correct": False},
            {"text": {"uz": "4"}, "is_correct": True},
        ],
    )

    assert question.order == 1
    assert question.choices.count() == 2
    assert question.choices.get(is_correct=True).text["uz"] == "4"


def test_single_choice_requires_exactly_one_correct_answer():
    quiz = QuizFactory()

    with pytest.raises(DomainError) as exc:
        services.add_question(
            quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "?"},
            choices=[
                {"text": {"uz": "A"}, "is_correct": True},
                {"text": {"uz": "B"}, "is_correct": True},
            ],
        )
    assert exc.value.code == "invalid_correct_count"


def test_multiple_choice_requires_at_least_one_correct():
    quiz = QuizFactory()

    with pytest.raises(DomainError) as exc:
        services.add_question(
            quiz=quiz, type=QuestionType.MULTIPLE_CHOICE, text={"uz": "?"},
            choices=[
                {"text": {"uz": "A"}, "is_correct": False},
                {"text": {"uz": "B"}, "is_correct": False},
            ],
        )
    assert exc.value.code == "invalid_correct_count"


def test_choice_question_requires_at_least_two_choices():
    quiz = QuizFactory()

    with pytest.raises(DomainError) as exc:
        services.add_question(
            quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "?"},
            choices=[{"text": {"uz": "Yagona"}, "is_correct": True}],
        )
    assert exc.value.code == "not_enough_choices"


def test_short_text_question_requires_pattern():
    quiz = QuizFactory()

    with pytest.raises(DomainError) as exc:
        services.add_question(quiz=quiz, type=QuestionType.SHORT_TEXT, text={"uz": "Django qaysi tilda?"})
    assert exc.value.code == "pattern_required"


def test_short_text_question_with_pattern_succeeds():
    quiz = QuizFactory()
    question = services.add_question(
        quiz=quiz, type=QuestionType.SHORT_TEXT, text={"uz": "Django qaysi tilda?"},
        correct_text_pattern="python",
    )
    assert question.choices.count() == 0
    assert question.correct_text_pattern == "python"


def test_questions_are_ordered_sequentially():
    quiz = QuizFactory()
    q1 = services.add_question(
        quiz=quiz, type=QuestionType.TRUE_FALSE, text={"uz": "1"},
        choices=[{"text": {"uz": "To'g'ri"}, "is_correct": True}, {"text": {"uz": "Noto'g'ri"}, "is_correct": False}],
    )
    q2 = services.add_question(
        quiz=quiz, type=QuestionType.TRUE_FALSE, text={"uz": "2"},
        choices=[{"text": {"uz": "To'g'ri"}, "is_correct": True}, {"text": {"uz": "Noto'g'ri"}, "is_correct": False}],
    )

    assert q1.order == 1
    assert q2.order == 2


# ---------------------------------------------------------------------------
# Tahrirlash / o'chirish
# ---------------------------------------------------------------------------

def test_update_question_replaces_choices():
    quiz = QuizFactory()
    question = services.add_question(
        quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "?"},
        choices=[{"text": {"uz": "A"}, "is_correct": True}, {"text": {"uz": "B"}, "is_correct": False}],
    )

    updated = services.update_question(
        question=question, text={"uz": "Yangi savol"},
        choices=[
            {"text": {"uz": "X"}, "is_correct": False},
            {"text": {"uz": "Y"}, "is_correct": True},
            {"text": {"uz": "Z"}, "is_correct": False},
        ],
    )

    assert updated.text["uz"] == "Yangi savol"
    assert updated.choices.count() == 3
    assert updated.choices.get(is_correct=True).text["uz"] == "Y"


def test_update_question_without_choices_keeps_existing_ones():
    quiz = QuizFactory()
    question = services.add_question(
        quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "?"},
        choices=[{"text": {"uz": "A"}, "is_correct": True}, {"text": {"uz": "B"}, "is_correct": False}],
    )

    updated = services.update_question(question=question, points=5)

    assert updated.points == 5
    assert updated.choices.count() == 2


def test_delete_question_removes_it_and_choices():
    quiz = QuizFactory()
    question = services.add_question(
        quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "?"},
        choices=[{"text": {"uz": "A"}, "is_correct": True}, {"text": {"uz": "B"}, "is_correct": False}],
    )
    question_id = question.id

    services.delete_question(question=question)

    from apps.assessments.models import Choice, Question

    assert not Question.objects.filter(id=question_id).exists()
    assert not Choice.objects.filter(question_id=question_id).exists()
