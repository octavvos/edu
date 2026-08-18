"""Davomat: belgilash qoidalari, kunlik varaqa va umumiy hisob."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.core.exceptions import DomainError
from apps.groups import services as group_services
from apps.groups.attendance import (
    get_attendance_sheet,
    get_attendance_summary,
    get_marked_dates,
)
from apps.groups.models import Attendance, AttendanceStatus
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def _admit(mentor, group):
    student = PendingUserFactory()
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student, group=group),
        mentor=mentor,
    )
    return student


def _mark(mentor, group, student, status, *, date=None, note=""):
    return group_services.mark_attendance(
        mentor=mentor, group=group, date=date or timezone.localdate(),
        records=[{"student_id": student.id, "status": status, "note": note}],
    )


# ---------------------------------------------------------------------------
# Belgilash
# ---------------------------------------------------------------------------

def test_mentor_marks_attendance_for_own_group():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)

    saved = _mark(mentor, group, student, AttendanceStatus.PRESENT, note="Vaqtida keldi")

    assert saved == 1
    record = Attendance.objects.get(group=group, student=student)
    assert record.status == AttendanceStatus.PRESENT
    assert record.note == "Vaqtida keldi"
    assert record.marked_by_id == mentor.id


def test_marking_same_day_twice_updates_instead_of_duplicating():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)

    _mark(mentor, group, student, AttendanceStatus.ABSENT)
    _mark(mentor, group, student, AttendanceStatus.LATE, note="Kechroq yetib keldi")

    assert Attendance.objects.filter(group=group, student=student).count() == 1
    record = Attendance.objects.get(group=group, student=student)
    assert record.status == AttendanceStatus.LATE
    assert record.note == "Kechroq yetib keldi"


def test_different_days_are_separate_records():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)
    today = timezone.localdate()

    _mark(mentor, group, student, AttendanceStatus.PRESENT, date=today)
    _mark(mentor, group, student, AttendanceStatus.ABSENT, date=today - timedelta(days=2))

    assert Attendance.objects.filter(group=group, student=student).count() == 2


def test_other_mentor_cannot_mark_attendance():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)

    with pytest.raises(DomainError) as exc:
        _mark(UserFactory(), group, student, AttendanceStatus.PRESENT)
    assert exc.value.status_code == 403


def test_cannot_mark_student_from_another_group():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    other_group = GroupFactory(mentor=mentor)
    outsider = _admit(mentor, other_group)

    with pytest.raises(DomainError) as exc:
        _mark(mentor, group, outsider, AttendanceStatus.PRESENT)
    assert exc.value.code == "not_a_member"


def test_removed_student_cannot_be_marked():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)
    group_services.remove_student(student=student, group=group, mentor=mentor)

    with pytest.raises(DomainError) as exc:
        _mark(mentor, group, student, AttendanceStatus.PRESENT)
    assert exc.value.code == "not_a_member"


def test_future_date_is_rejected():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)

    with pytest.raises(DomainError) as exc:
        _mark(mentor, group, student, AttendanceStatus.PRESENT,
              date=timezone.localdate() + timedelta(days=1))
    assert exc.value.code == "future_date"


def test_invalid_status_is_rejected():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)

    with pytest.raises(DomainError) as exc:
        _mark(mentor, group, student, "kelmadimi")
    assert exc.value.code == "invalid_status"


# ---------------------------------------------------------------------------
# Kunlik varaqa
# ---------------------------------------------------------------------------

def test_sheet_lists_all_active_members_even_unmarked():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    marked_student = _admit(mentor, group)
    _admit(mentor, group)  # belgilanmagan

    _mark(mentor, group, marked_student, AttendanceStatus.PRESENT)

    rows = get_attendance_sheet(group, timezone.localdate())
    assert len(rows) == 2
    by_id = {r.student_id: r for r in rows}
    assert by_id[str(marked_student.id)].status == AttendanceStatus.PRESENT
    assert [r.status for r in rows].count(None) == 1


def test_sheet_for_another_date_is_empty_of_marks():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)
    _mark(mentor, group, student, AttendanceStatus.PRESENT)

    rows = get_attendance_sheet(group, timezone.localdate() - timedelta(days=1))
    assert [r.status for r in rows] == [None]


def test_marked_dates_are_returned_newest_first():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)
    today = timezone.localdate()

    _mark(mentor, group, student, AttendanceStatus.PRESENT, date=today - timedelta(days=3))
    _mark(mentor, group, student, AttendanceStatus.ABSENT, date=today)

    assert get_marked_dates(group) == [today, today - timedelta(days=3)]


# ---------------------------------------------------------------------------
# Umumiy hisob
# ---------------------------------------------------------------------------

def test_summary_counts_each_status_and_computes_percent():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = _admit(mentor, group)
    today = timezone.localdate()

    _mark(mentor, group, student, AttendanceStatus.PRESENT, date=today)
    _mark(mentor, group, student, AttendanceStatus.LATE, date=today - timedelta(days=1))
    _mark(mentor, group, student, AttendanceStatus.ABSENT, date=today - timedelta(days=2))
    _mark(mentor, group, student, AttendanceStatus.EXCUSED, date=today - timedelta(days=3))

    row = get_attendance_summary(group)[0]
    assert (row.present, row.late, row.excused, row.absent) == (1, 1, 1, 1)
    assert row.total == 4
    # kelgan + kechikkan + sababli = 3 / 4
    assert row.attendance_percent == 75.0


def test_summary_includes_students_without_any_record():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    _admit(mentor, group)

    row = get_attendance_summary(group)[0]
    assert row.total == 0
    assert row.attendance_percent == 0.0


def test_summary_is_empty_for_group_without_members():
    mentor = UserFactory()
    assert get_attendance_summary(GroupFactory(mentor=mentor)) == []
