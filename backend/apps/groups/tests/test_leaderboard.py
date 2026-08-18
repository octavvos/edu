"""Guruh reytingi — baholangan ballar yig'indisi bo'yicha tartib."""

import pytest

from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.assignments import services as assignment_services
from apps.assignments.tests.factories import HomeworkFactory
from apps.enrollment.selectors import get_enrollment
from apps.groups import services as group_services
from apps.groups.leaderboard import get_group_leaderboard
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def _admit(mentor, group):
    student = PendingUserFactory()
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student, group=group),
        mentor=mentor,
    )
    return student


def _grade(student, group, score):
    homework = HomeworkFactory(lesson__module__course=group.course, group=group)
    enrollment = get_enrollment(user=student, course=group.course)
    submission = assignment_services.submit_homework(
        user=student, enrollment=enrollment, homework=homework, text="Bajardim",
    )
    assignment_services.grade_submission(mentor=group.mentor, submission=submission, score=score)


def test_leaderboard_sums_scores_across_multiple_gradings():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)

    _grade(student, group, 80)
    _grade(student, group, 70)

    rows = get_group_leaderboard(group)
    assert len(rows) == 1
    assert rows[0].total_score == 150
    assert rows[0].graded_count == 2
    assert rows[0].rank == 1


def test_leaderboard_ranks_higher_score_first():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    top_student = _admit(mentor, group)
    low_student = _admit(mentor, group)

    _grade(top_student, group, 95)
    _grade(low_student, group, 40)

    rows = get_group_leaderboard(group)
    assert [r.student_id for r in rows] == [str(top_student.id), str(low_student.id)]
    assert [r.rank for r in rows] == [1, 2]


def test_leaderboard_includes_ungraded_students_at_zero():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    graded_student = _admit(mentor, group)
    ungraded_student = _admit(mentor, group)

    _grade(graded_student, group, 60)

    rows = get_group_leaderboard(group)
    assert len(rows) == 2
    ungraded_row = next(r for r in rows if r.student_id == str(ungraded_student.id))
    assert ungraded_row.total_score == 0
    assert ungraded_row.graded_count == 0
    assert ungraded_row.rank == 2  # ballsizlar pastda


def test_leaderboard_excludes_other_groups():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    other_group = GroupFactory(mentor=mentor)
    _admit(mentor, group)
    _admit(mentor, other_group)

    assert len(get_group_leaderboard(group)) == 1
    assert len(get_group_leaderboard(other_group)) == 1


def test_leaderboard_empty_for_group_without_members():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)

    assert get_group_leaderboard(group) == []
