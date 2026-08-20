import pytest

from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.assessments import selectors, services
from apps.assessments.models import Choice, Question, QuestionType, Quiz
from apps.courses.tests.factories import CourseFactory, LessonFactory, ModuleFactory
from apps.groups import services as group_services
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def _make_quiz(course):
    module = ModuleFactory(course=course)
    lesson = LessonFactory(module=module, type="quiz", title={"uz": "1-modul testi"})
    quiz = Quiz.objects.create(lesson=lesson, pass_percent=60, max_attempts=2, time_limit_seconds=900)
    question = Question.objects.create(quiz=quiz, type=QuestionType.SINGLE_CHOICE, text={"uz": "2+2=?"}, points=1)
    correct = Choice.objects.create(question=question, text={"uz": "4"}, is_correct=True, order=1)
    Choice.objects.create(question=question, text={"uz": "5"}, is_correct=False, order=2)
    return lesson, quiz, question, correct


def _admit(mentor, group):
    student = PendingUserFactory()
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student, group=group),
        mentor=mentor,
    )
    return student


def test_get_my_quizzes_lists_only_tests_sent_to_own_group():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    group = GroupFactory(course=course, mentor=mentor)
    student = _admit(mentor, group)
    lesson, quiz, question, correct = _make_quiz(course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)

    results = selectors.get_my_quizzes(student)

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


def test_get_my_quizzes_hides_tests_not_sent_to_group():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    group = GroupFactory(course=course, mentor=mentor)
    student = _admit(mentor, group)
    _make_quiz(course)
    # assign_quiz_to_group chaqirilmadi — test hali yuborilmagan

    assert selectors.get_my_quizzes(student) == []


def test_get_my_quizzes_excludes_students_without_group():
    user = UserFactory()
    course = CourseFactory(price=0)
    _, quiz, _, _ = _make_quiz(course)
    mentor = UserFactory()
    group = GroupFactory(course=course, mentor=mentor)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)
    # `user` hech qaysi guruhga a'zo emas

    assert selectors.get_my_quizzes(user) == []


def test_get_my_quizzes_reflects_best_score_and_in_progress():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    group = GroupFactory(course=course, mentor=mentor)
    student = _admit(mentor, group)
    lesson, quiz, question, correct = _make_quiz(course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)

    from apps.enrollment.models import Enrollment

    enrollment = Enrollment.objects.get(user=student, course=course)
    attempt = services.start_attempt(user=student, enrollment=enrollment, quiz=quiz)
    services.submit_answer(attempt=attempt, question=question, selected_choice_ids=[str(correct.id)])
    services.finalize_attempt(attempt=attempt)

    second_attempt = services.start_attempt(user=student, enrollment=enrollment, quiz=quiz)

    row = selectors.get_my_quizzes(student)[0]
    assert row["attempt_count"] == 2
    assert row["best_score"] == 100.0
    assert row["passed"] is True
    assert row["has_in_progress"] is True
    assert row["in_progress_attempt_id"] == str(second_attempt.id)


# ---------------------------------------------------------------------------
# Mentor: test natijalari tahlili
# ---------------------------------------------------------------------------


def _solve(student, quiz, question, *, select=None):
    """`select` — javob sifatida belgilanadigan Choice (None bo'lsa javobsiz qoldiriladi)."""
    from apps.enrollment.models import Enrollment

    enrollment = Enrollment.objects.get(user=student, course=quiz.lesson.module.course)
    attempt = services.start_attempt(user=student, enrollment=enrollment, quiz=quiz)
    selected = [str(select.id)] if select else []
    services.submit_answer(attempt=attempt, question=question, selected_choice_ids=selected)
    return services.finalize_attempt(attempt=attempt)


def test_get_groups_with_quiz_results_lists_only_groups_with_sent_tests():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    sent_group = GroupFactory(course=course, mentor=mentor)
    unsent_group = GroupFactory(course=course, mentor=mentor)
    _admit(mentor, sent_group)
    _, quiz, _, _ = _make_quiz(course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=sent_group)

    rows = selectors.get_groups_with_quiz_results(mentor)

    assert [r.group_id for r in rows] == [str(sent_group.id)]
    assert unsent_group.id != sent_group.id
    row = rows[0]
    assert row.tests_sent == 1
    assert row.student_count == 1
    assert row.avg_score is None
    assert row.completion_percent == 0.0


def test_get_groups_with_quiz_results_reflects_submitted_attempts():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    group = GroupFactory(course=course, mentor=mentor)
    student = _admit(mentor, group)
    lesson, quiz, question, correct = _make_quiz(course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)
    _solve(student, quiz, question, select=correct)

    row = selectors.get_groups_with_quiz_results(mentor)[0]

    assert row.avg_score == 100.0
    assert row.completion_percent == 100.0


def test_get_group_quiz_leaderboard_ranks_by_avg_score():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    group = GroupFactory(course=course, mentor=mentor)
    top_student = _admit(mentor, group)
    low_student = _admit(mentor, group)
    lesson, quiz, question, correct = _make_quiz(course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)

    _solve(top_student, quiz, question, select=correct)
    _solve(low_student, quiz, question, select=None)

    rows = selectors.get_group_quiz_leaderboard(group)

    assert [r.student_id for r in rows] == [str(top_student.id), str(low_student.id)]
    assert rows[0].rank == 1
    assert rows[0].avg_score == 100.0
    assert rows[0].tests_solved == 1
    assert rows[1].rank == 2
    assert rows[1].avg_score == 0.0


def test_get_student_quiz_results_reports_per_test_outcome():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    group = GroupFactory(course=course, mentor=mentor)
    student = _admit(mentor, group)
    lesson, quiz, question, correct = _make_quiz(course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)
    attempt = _solve(student, quiz, question, select=correct)

    rows = selectors.get_student_quiz_results(group, student)

    assert len(rows) == 1
    row = rows[0]
    assert row.lesson_id == str(lesson.id)
    assert row.status == "passed"
    assert row.score_percent == 100.0
    assert row.attempt_id == str(attempt.id)
    assert row.attempt_count == 1
    assert row.time_taken_seconds is not None


def test_get_attempt_detail_reports_selected_and_correct_choices():
    mentor = UserFactory()
    course = CourseFactory(price=0)
    group = GroupFactory(course=course, mentor=mentor)
    student = _admit(mentor, group)
    lesson, quiz, question, correct = _make_quiz(course)
    services.assign_quiz_to_group(mentor=mentor, quiz=quiz, group=group)
    wrong = question.choices.exclude(id=correct.id).first()
    attempt = _solve(student, quiz, question, select=wrong)  # student ataylab noto'g'ri variantni tanlaydi

    detail = selectors.get_attempt_detail(attempt)

    assert detail.attempt_id == str(attempt.id)
    assert detail.student_display_name == student.display_name
    assert len(detail.answers) == 1
    answer_row = detail.answers[0]
    assert answer_row.selected_choice_ids == [str(wrong.id)]
    assert answer_row.selected_texts == ["5"]
    assert answer_row.correct_choice_ids == [str(correct.id)]
    assert answer_row.correct_texts == ["4"]
    assert answer_row.is_correct is False
