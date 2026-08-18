"""Mentor uy vazifalarini boshqarishi: taqsimlash, holat o'tishlari, baholash."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.assignments import services
from apps.assignments.models import SubmissionStatus
from apps.assignments.tests.factories import HomeworkFactory
from apps.core.exceptions import DomainError
from apps.enrollment.selectors import get_enrollment
from apps.groups import services as group_services
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def _student_in_group_of(mentor, *, course=None):
    """Mentorning guruhiga qabul qilingan o'quvchi qaytaradi."""
    group = GroupFactory(mentor=mentor, **({"course": course} if course else {}))
    student = PendingUserFactory()
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student, group=group),
        mentor=mentor,
    )
    return student, group


def _submit(student, group, **homework_kwargs):
    homework = HomeworkFactory(lesson__module__course=group.course, **homework_kwargs)
    enrollment = get_enrollment(user=student, course=group.course)
    return services.submit_homework(
        user=student, enrollment=enrollment, homework=homework, text="Bajardim",
    )


# ---------------------------------------------------------------------------
# Mentorga taqsimlash
# ---------------------------------------------------------------------------

def test_submission_is_assigned_to_the_mentor_of_students_group():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    submission = _submit(student, group)

    assert submission.mentor_id == mentor.id
    assert submission.status == SubmissionStatus.SUBMITTED


def test_submission_requires_some_content():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    homework = HomeworkFactory(lesson__module__course=group.course)
    enrollment = get_enrollment(user=student, course=group.course)

    with pytest.raises(DomainError) as exc:
        services.submit_homework(user=student, enrollment=enrollment, homework=homework)
    assert exc.value.code == "empty_submission"


def test_late_submission_is_flagged():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    submission = _submit(student, group, deadline_at=timezone.now() - timedelta(days=1))

    assert submission.is_late is True


def test_submission_before_deadline_is_not_late():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    submission = _submit(student, group, deadline_at=timezone.now() + timedelta(days=1))

    assert submission.is_late is False


# ---------------------------------------------------------------------------
# Holat o'tishlari (H-03)
# ---------------------------------------------------------------------------

def test_mentor_can_move_submission_to_under_review():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    updated = services.change_submission_status(
        mentor=mentor, submission=submission, new_status=SubmissionStatus.UNDER_REVIEW,
    )
    assert updated.status == SubmissionStatus.UNDER_REVIEW


def test_accepted_submission_cannot_change_status():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)
    services.grade_submission(mentor=mentor, submission=submission, score=90)

    with pytest.raises(DomainError) as exc:
        services.change_submission_status(
            mentor=mentor, submission=submission, new_status=SubmissionStatus.UNDER_REVIEW,
        )
    assert exc.value.code == "invalid_transition"


def test_cannot_accept_without_grading():
    """'Qabul qilindi' holatiga faqat baho orqali o'tiladi."""
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.change_submission_status(
            mentor=mentor, submission=submission, new_status=SubmissionStatus.ACCEPTED,
        )
    assert exc.value.code == "grade_required"


def test_other_mentor_cannot_review_submission():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.change_submission_status(
            mentor=UserFactory(), submission=submission,
            new_status=SubmissionStatus.UNDER_REVIEW,
        )
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Baholash (H-04)
# ---------------------------------------------------------------------------

def test_grading_accepts_submission_and_stores_feedback():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    updated = services.grade_submission(
        mentor=mentor, submission=submission, score=85, feedback="Yaxshi ish",
    )

    assert updated.status == SubmissionStatus.ACCEPTED
    assert updated.grade.score == 85
    assert updated.grade.feedback == "Yaxshi ish"


def test_grading_with_needs_revision_sends_back():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    updated = services.grade_submission(
        mentor=mentor, submission=submission, score=40,
        feedback="Qayta ishlang", needs_revision=True,
    )

    assert updated.status == SubmissionStatus.NEEDS_REVISION
    assert updated.grade.score == 40


@pytest.mark.parametrize("score", [-1, 101])
def test_score_outside_zero_to_hundred_is_rejected(score):
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.grade_submission(mentor=mentor, submission=submission, score=score)
    assert exc.value.code == "invalid_score"


def test_already_accepted_submission_cannot_be_regraded():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)
    services.grade_submission(mentor=mentor, submission=submission, score=90)

    with pytest.raises(DomainError) as exc:
        services.grade_submission(mentor=mentor, submission=submission, score=50)
    assert exc.value.code == "already_accepted"


def test_other_mentor_cannot_grade():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.grade_submission(mentor=UserFactory(), submission=submission, score=90)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Mentor navbati
# ---------------------------------------------------------------------------

def test_mentor_queue_shows_only_own_students_and_hides_accepted():
    from apps.assignments.selectors import get_mentor_queue

    mentor = UserFactory()
    other_mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    other_student, other_group = _student_in_group_of(other_mentor)

    mine = _submit(student, group)
    _submit(other_student, other_group)

    assert list(get_mentor_queue(mentor)) == [mine]

    services.grade_submission(mentor=mentor, submission=mine, score=100)
    assert list(get_mentor_queue(mentor)) == []


def test_mentor_queue_puts_late_submissions_first():
    from apps.assignments.selectors import get_mentor_queue

    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    _submit(student, group)  # o'z vaqtida
    late = _submit(student, group, deadline_at=timezone.now() - timedelta(days=2))

    assert get_mentor_queue(mentor).first() == late
