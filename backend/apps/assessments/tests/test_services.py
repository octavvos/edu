import pytest

from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.assessments import services
from apps.assessments.models import Choice, Question, QuestionType, Quiz, QuizAssignment
from apps.core.exceptions import DomainError
from apps.courses.tests.factories import CourseFactory, LessonFactory, ModuleFactory
from apps.enrollment.services import enroll_free
from apps.groups import services as group_services
from apps.groups.tests.factories import GroupFactory

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


# ---------------------------------------------------------------------------
# Testni guruhga jo'natish (mentor tanlab yuboradi, o'quvchi shu guruhda bo'lsa ko'radi)
# ---------------------------------------------------------------------------

def _student_in_group_of(mentor, *, course=None):
    group = GroupFactory(mentor=mentor, **({"course": course} if course else {}))
    student = PendingUserFactory()
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student, group=group),
        mentor=mentor,
    )
    return student, group


def _make_quiz_in_course(course):
    module = ModuleFactory(course=course)
    lesson = LessonFactory(module=module, type="quiz")
    quiz = Quiz.objects.create(lesson=lesson, pass_percent=60, max_attempts=3)
    question = Question.objects.create(quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "2+2=?"}, points=1)
    correct = Choice.objects.create(question=question, text={"uz": "4"}, is_correct=True, order=1)
    return quiz, question, correct


def test_assign_quiz_to_group_creates_assignment():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    quiz, question, correct = _make_quiz_in_course(group.course)

    assignment = services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)

    assert assignment.quiz_id == quiz.id
    assert assignment.group_id == group.id
    assert QuizAssignment.objects.filter(quiz=quiz, group=group).count() == 1


def test_assign_quiz_to_group_is_idempotent():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    quiz, question, correct = _make_quiz_in_course(group.course)

    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)

    assert QuizAssignment.objects.filter(quiz=quiz, group=group).count() == 1


def test_assign_quiz_to_group_rejects_another_mentors_group():
    mentor = UserFactory()
    _, own_group = _student_in_group_of(mentor)
    quiz, question, correct = _make_quiz_in_course(own_group.course)
    other_group = GroupFactory(mentor=UserFactory(), course=own_group.course)

    with pytest.raises(DomainError) as exc:
        services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=other_group)
    assert exc.value.code == "not_your_group"


def test_assign_quiz_to_group_rejects_group_from_another_course():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    quiz, question, correct = _make_quiz_in_course(group.course)
    foreign_group = GroupFactory(mentor=mentor)  # boshqa kursning guruhi

    with pytest.raises(DomainError) as exc:
        services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=foreign_group)
    assert exc.value.code == "group_course_mismatch"


def test_unassign_quiz_from_group_removes_it():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    quiz, question, correct = _make_quiz_in_course(group.course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)

    services.unassign_quiz_from_group(mentor=mentor, quiz=quiz, group=group)

    assert QuizAssignment.objects.filter(quiz=quiz, group=group).exists() is False


def test_assert_quiz_visible_to_student_passes_when_assigned():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    quiz, question, correct = _make_quiz_in_course(group.course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)

    services.assert_quiz_visible_to_student(user=student, quiz=quiz)  # raise qilmasligi kerak


def test_assert_quiz_visible_to_student_rejects_unassigned_quiz():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    quiz, question, correct = _make_quiz_in_course(group.course)
    # assign_quiz_to_group chaqirilmadi

    with pytest.raises(services.AssessmentError) as exc:
        services.assert_quiz_visible_to_student(user=student, quiz=quiz)
    assert exc.value.code == "quiz_not_assigned"
