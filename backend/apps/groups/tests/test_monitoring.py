"""O'quvchilar monitoringi: progress, faollik va xavf mezonlari."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.enrollment.models import Enrollment
from apps.groups import services as group_services
from apps.groups.models import GroupMembership
from apps.groups.monitoring import GRACE_DAYS, INACTIVE_DAYS, get_students_overview
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def _admit(mentor, *, group=None, last_login=None, progress=100.0):
    """Mentor guruhiga o'quvchi qabul qiladi va progressini belgilaydi."""
    group = group or GroupFactory(mentor=mentor)
    student = PendingUserFactory(last_login=last_login)
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student, group=group),
        mentor=mentor,
    )
    Enrollment.objects.filter(user=student, course=group.course).update(progress_percent=progress)
    return student, group


def _age_membership(student, days):
    """A'zolikni eskirtiradi (auto_now_add ni chetlab o'tish uchun update)."""
    GroupMembership.objects.filter(student=student).update(
        joined_at=timezone.now() - timedelta(days=days),
    )


def test_overview_lists_only_own_students():
    mentor = UserFactory()
    student, _ = _admit(mentor, last_login=timezone.now())
    _admit(UserFactory(), last_login=timezone.now())  # boshqa mentorning o'quvchisi

    rows = get_students_overview(mentor)

    assert [r.username for r in rows] == [student.username]


def test_active_student_with_good_progress_is_not_at_risk():
    mentor = UserFactory()
    student, _ = _admit(mentor, last_login=timezone.now(), progress=80.0)
    _age_membership(student, 30)

    row = get_students_overview(mentor)[0]

    assert row.at_risk is False
    assert row.risk_reasons == []
    assert row.progress_percent == 80.0


def test_student_who_never_logged_in_is_at_risk():
    mentor = UserFactory()
    _admit(mentor, last_login=None)

    row = get_students_overview(mentor)[0]

    assert row.at_risk is True
    assert row.last_login is None
    assert "Hech qachon tizimga kirmagan" in row.risk_reasons


def test_long_inactive_student_is_at_risk():
    mentor = UserFactory()
    _admit(mentor, last_login=timezone.now() - timedelta(days=INACTIVE_DAYS + 1))

    row = get_students_overview(mentor)[0]

    assert row.at_risk is True
    assert row.days_since_login >= INACTIVE_DAYS
    assert any("kirmagan" in reason for reason in row.risk_reasons)


def test_recently_active_student_is_not_flagged_for_inactivity():
    mentor = UserFactory()
    student, _ = _admit(mentor, last_login=timezone.now() - timedelta(days=INACTIVE_DAYS - 1))
    _age_membership(student, 30)

    row = get_students_overview(mentor)[0]

    assert not any("kirmagan" in reason for reason in row.risk_reasons)


def test_low_progress_flags_established_student():
    mentor = UserFactory()
    student, _ = _admit(mentor, last_login=timezone.now(), progress=10.0)
    _age_membership(student, GRACE_DAYS + 1)

    row = get_students_overview(mentor)[0]

    assert row.at_risk is True
    assert any("Progress past" in reason for reason in row.risk_reasons)


def test_new_student_gets_grace_period_for_low_progress():
    """Yangi qo'shilgan o'quvchi past progress uchun xavf deb belgilanmaydi."""
    mentor = UserFactory()
    _admit(mentor, last_login=timezone.now(), progress=0.0)  # bugun qo'shilgan

    row = get_students_overview(mentor)[0]

    assert row.at_risk is False


def test_overdue_submission_flags_student():
    from apps.assignments.tests.factories import HomeworkFactory
    from apps.assignments import services as assignment_services
    from apps.enrollment.selectors import get_enrollment

    mentor = UserFactory()
    student, group = _admit(mentor, last_login=timezone.now(), progress=90.0)
    _age_membership(student, 30)

    homework = HomeworkFactory(
        lesson__module__course=group.course, group=group,
        deadline_at=timezone.now() - timedelta(days=3),
    )
    assignment_services.submit_homework(
        user=student, enrollment=get_enrollment(user=student, course=group.course),
        homework=homework, text="Kech topshirdim",
    )

    row = get_students_overview(mentor)[0]

    assert row.overdue_submissions == 1
    assert row.at_risk is True
    assert any("kechikkan" in reason for reason in row.risk_reasons)


def test_at_risk_students_are_listed_first():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    healthy, _ = _admit(mentor, group=group, last_login=timezone.now(), progress=95.0)
    at_risk, _ = _admit(mentor, group=group, last_login=None, progress=5.0)
    _age_membership(healthy, 30)

    rows = get_students_overview(mentor)

    assert rows[0].username == at_risk.username
    assert rows[0].at_risk is True
    assert rows[1].at_risk is False


def test_group_filter_narrows_results():
    mentor = UserFactory()
    group_a = GroupFactory(mentor=mentor)
    group_b = GroupFactory(mentor=mentor)
    student_a, _ = _admit(mentor, group=group_a, last_login=timezone.now())
    _admit(mentor, group=group_b, last_login=timezone.now())

    rows = get_students_overview(mentor, group_id=group_a.id)

    assert [r.username for r in rows] == [student_a.username]
