import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments import selectors, services
from apps.assessments.models import Choice, Question, QuestionType, Quiz
from apps.courses.tests.factories import CourseFactory, LessonFactory, ModuleFactory
from apps.enrollment.services import enroll_free

pytestmark = pytest.mark.django_db


def _make_quiz(course):
    module = ModuleFactory(course=course)
    lesson = LessonFactory(module=module, type="quiz", title={"uz": "1-modul testi"})
    quiz = Quiz.objects.create(lesson=lesson, pass_percent=60, max_attempts=2, time_limit_seconds=900)
    question = Question.objects.create(quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "2+2=?"}, points=1)
    correct = Choice.objects.create(question=question, text={"uz": "4"}, is_correct=True, order=1)
    Choice.objects.create(question=question, text={"uz": "5"}, is_correct=False, order=2)
    return lesson, quiz, question, correct


def test_get_my_quizzes_lists_enrolled_course_tests():
    user = UserFactory()
    course = CourseFactory(price=0)
    lesson, quiz, question, correct = _make_quiz(course)
    enroll_free(user=user, course=course)

    results = selectors.get_my_quizzes(user)

    assert len(results) == 1
    row = results[0]
    assert row["lesson_id"] == str(lesson.id)
    assert row["title"] == "1-modul testi"
    assert row["question_count"] == 1
    assert row["time_limit_seconds"] == 900
    assert row["attempt_count"] == 0
    assert row["best_score"] is None
    assert row["passed"] is False
    assert row["has_in_progress"] is False


def test_get_my_quizzes_excludes_unenrolled_courses():
    user = UserFactory()
    course = CourseFactory(price=0)
    _make_quiz(course)
    # enrollment yo'q — test ro'yxatda ko'rinmasligi kerak

    assert selectors.get_my_quizzes(user) == []


def test_get_my_quizzes_reflects_best_score_and_in_progress():
    user = UserFactory()
    course = CourseFactory(price=0)
    lesson, quiz, question, correct = _make_quiz(course)
    enrollment = enroll_free(user=user, course=course)

    attempt = services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)
    services.submit_answer(attempt=attempt, question=question, selected_choice_ids=[str(correct.id)])
    services.finalize_attempt(attempt=attempt)

    second_attempt = services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)

    row = selectors.get_my_quizzes(user)[0]
    assert row["attempt_count"] == 2
    assert row["best_score"] == 100.0
    assert row["passed"] is True
    assert row["has_in_progress"] is True
    assert row["in_progress_attempt_id"] == str(second_attempt.id)
