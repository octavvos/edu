import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments import services
from apps.assessments.models import Choice, Question, QuestionType, Quiz
from apps.courses.tests.factories import CourseFactory, LessonFactory, ModuleFactory
from apps.enrollment.services import enroll_free

pytestmark = pytest.mark.django_db


def _make_quiz_with_single_choice_question(pass_percent=60):
    course = CourseFactory(price=0)
    module = ModuleFactory(course=course)
    lesson = LessonFactory(module=module, type="quiz")
    quiz = Quiz.objects.create(lesson=lesson, pass_percent=pass_percent, max_attempts=3)
    question = Question.objects.create(quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "2+2=?"}, points=1)
    correct = Choice.objects.create(question=question, text={"uz": "4"}, is_correct=True, order=1)
    Choice.objects.create(question=question, text={"uz": "5"}, is_correct=False, order=2)
    return course, quiz, question, correct


def test_correct_answer_passes_quiz_and_completes_lesson():
    user = UserFactory()
    course, quiz, question, correct = _make_quiz_with_single_choice_question()
    enrollment = enroll_free(user=user, course=course)

    attempt = services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)
    services.submit_answer(attempt=attempt, question=question, selected_choice_ids=[str(correct.id)])
    attempt = services.finalize_attempt(attempt=attempt)

    assert attempt.passed is True
    assert attempt.score_percent == 100.0


def test_wrong_answer_fails_quiz():
    user = UserFactory()
    course, quiz, question, correct = _make_quiz_with_single_choice_question()
    wrong_choice = question.choices.exclude(id=correct.id).first()
    enrollment = enroll_free(user=user, course=course)

    attempt = services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)
    services.submit_answer(attempt=attempt, question=question, selected_choice_ids=[str(wrong_choice.id)])
    attempt = services.finalize_attempt(attempt=attempt)

    assert attempt.passed is False
    assert attempt.score_percent == 0.0


def test_max_attempts_enforced():
    user = UserFactory()
    course, quiz, question, correct = _make_quiz_with_single_choice_question()
    quiz.max_attempts = 1
    quiz.save(update_fields=["max_attempts"])
    enrollment = enroll_free(user=user, course=course)

    attempt = services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)
    services.finalize_attempt(attempt=attempt)

    with pytest.raises(services.AssessmentError):
        services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)


def test_submit_answer_accepts_uuid_objects():
    """DRF UUIDField client javobni Python UUID obyekti sifatida uzatadi — JSONField
    ularni to'g'ridan-to'g'ri saqlay olmaydi, shuning uchun submit_answer matnga
    o'girishi shart (avval TypeError bilan qulagan)."""
    user = UserFactory()
    course, quiz, question, correct = _make_quiz_with_single_choice_question()
    enrollment = enroll_free(user=user, course=course)

    attempt = services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)
    answer = services.submit_answer(attempt=attempt, question=question, selected_choice_ids=[correct.id])

    assert answer.selected_choice_ids == [str(correct.id)]
    assert answer.is_correct is True


def test_unanswered_questions_count_toward_score():
    """Javobsiz qoldirilgan savol ham maxrajga kiradi — aks holda bitta savolga
    to'g'ri javob berib, qolganini o'tkazib yuborish 100% bergan bo'lardi."""
    user = UserFactory()
    course, quiz, question, correct = _make_quiz_with_single_choice_question()
    second_question = Question.objects.create(
        quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "3+3=?"}, points=1,
    )
    Choice.objects.create(question=second_question, text={"uz": "6"}, is_correct=True, order=1)
    Choice.objects.create(question=second_question, text={"uz": "7"}, is_correct=False, order=2)
    enrollment = enroll_free(user=user, course=course)

    attempt = services.start_attempt(user=user, enrollment=enrollment, quiz=quiz)
    services.submit_answer(attempt=attempt, question=question, selected_choice_ids=[str(correct.id)])
    # second_question ataylab javobsiz qoldiriladi
    attempt = services.finalize_attempt(attempt=attempt)

    assert attempt.score_percent == 50.0
    assert attempt.passed is False
