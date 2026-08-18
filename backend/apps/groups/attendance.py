"""
Davomat o'qish qatlami: kunlik varaqa va o'quvchi bo'yicha umumiy hisob.

`monitoring.py` va `leaderboard.py` kabi alohida modulda — bu bir necha
manbadan (a'zolik + davomat yozuvlari) yig'iladigan ko'rinish, `selectors.py`
ni og'irlashtirmasligi uchun.
"""

from dataclasses import dataclass

from django.db.models import Count, Q


@dataclass
class AttendanceRow:
    """Kunlik varaqadagi bitta o'quvchi qatori."""

    student_id: str
    username: str
    display_name: str
    status: str | None      # shu kunga hali belgilanmagan bo'lsa None
    note: str


@dataclass
class AttendanceSummaryRow:
    """O'quvchining butun davr bo'yicha davomat hisobi."""

    student_id: str
    username: str
    display_name: str
    present: int
    late: int
    excused: int
    absent: int
    total: int
    attendance_percent: float


def get_attendance_sheet(group, date) -> list[AttendanceRow]:
    """Guruhning shu sanadagi varaqasi — faol a'zolar + mavjud belgilar."""
    from apps.groups.models import Attendance, GroupMembership, MembershipStatus

    memberships = (
        GroupMembership.objects.filter(group=group, status=MembershipStatus.ACTIVE)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )
    marked = {
        a.student_id: a
        for a in Attendance.objects.filter(group=group, date=date)
    }

    rows = []
    for membership in memberships:
        student = membership.student
        record = marked.get(student.id)
        rows.append(AttendanceRow(
            student_id=str(student.id),
            username=student.username,
            display_name=student.display_name,
            status=record.status if record else None,
            note=record.note if record else "",
        ))
    return rows


def get_attendance_summary(group) -> list[AttendanceSummaryRow]:
    """Guruh bo'yicha umumiy davomat — kim qancha kelgan/kelmagan."""
    from apps.groups.models import Attendance, AttendanceStatus, GroupMembership, MembershipStatus

    memberships = (
        GroupMembership.objects.filter(group=group, status=MembershipStatus.ACTIVE)
        .select_related("student")
    )
    student_ids = [m.student_id for m in memberships]
    if not student_ids:
        return []

    rows_by_student = {
        row["student_id"]: row
        for row in (
            Attendance.objects.filter(group=group, student_id__in=student_ids)
            .values("student_id")
            .annotate(
                present=Count("id", filter=Q(status=AttendanceStatus.PRESENT)),
                late=Count("id", filter=Q(status=AttendanceStatus.LATE)),
                excused=Count("id", filter=Q(status=AttendanceStatus.EXCUSED)),
                absent=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
            )
        )
    }

    result = []
    for membership in memberships:
        student = membership.student
        agg = rows_by_student.get(student.id, {})
        present = agg.get("present", 0)
        late = agg.get("late", 0)
        excused = agg.get("excused", 0)
        absent = agg.get("absent", 0)
        total = present + late + excused + absent
        # Kechikkan ham darsda qatnashgan hisoblanadi; sababli ham hurmatli sabab.
        attended = present + late + excused
        result.append(AttendanceSummaryRow(
            student_id=str(student.id),
            username=student.username,
            display_name=student.display_name,
            present=present, late=late, excused=excused, absent=absent,
            total=total,
            attendance_percent=round(attended / total * 100, 1) if total else 0.0,
        ))

    result.sort(key=lambda r: (-r.attendance_percent, r.display_name.lower()))
    return result


def get_marked_dates(group, limit: int = 30) -> list:
    """Shu guruhda davomat olingan sanalar — yaqindan uzoqqa."""
    from apps.groups.models import Attendance

    return list(
        Attendance.objects.filter(group=group)
        .values_list("date", flat=True)
        .distinct()
        .order_by("-date")[:limit],
    )
