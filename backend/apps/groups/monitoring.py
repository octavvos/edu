"""
Mentor uchun o'quvchilar monitoringi: progress, faollik va
"xavf ostidagi" o'quvchilarni aniqlash.

Alohida modulda, chunki bu bir nechta bounded context'dan (groups,
enrollment, assignments, accounts) ma'lumot yig'adigan o'qish qatlami —
uni `selectors.py` ichiga qo'shish o'sha modulni og'irlashtirardi.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from django.utils import timezone

# --- "Xavf ostida" mezonlari ------------------------------------------------
# Bu qiymatlar mahsulot qarori: mentor e'tibor berishi kerak bo'lgan chegara.
INACTIVE_DAYS = 14          # shuncha kundan beri kirmagan
LOW_PROGRESS_PERCENT = 30   # progress shundan past bo'lsa
GRACE_DAYS = 14             # yangi o'quvchiga past progress uchun beriladigan muhlat


@dataclass
class StudentRow:
    """Mentor jadvalidagi bitta o'quvchi qatori."""

    id: str
    username: str
    display_name: str
    group_id: str
    group_name: str
    joined_at: object
    last_login: object | None
    days_since_login: int | None
    progress_percent: float
    completed_lessons: int
    pending_submissions: int
    overdue_submissions: int
    at_risk: bool = False
    risk_reasons: list[str] = field(default_factory=list)


def get_students_overview(mentor, *, group_id=None) -> list[StudentRow]:
    """Mentorning barcha guruhlaridagi o'quvchilar va ularning holati."""
    from apps.assignments.models import Submission, SubmissionStatus
    from apps.enrollment.models import Enrollment
    from apps.groups.models import GroupMembership, MembershipStatus

    memberships = (
        GroupMembership.objects.filter(
            group__mentor=mentor, status=MembershipStatus.ACTIVE,
        )
        .select_related("student", "group")
        .order_by("group__name", "student__last_name", "student__first_name")
    )
    if group_id:
        memberships = memberships.filter(group_id=group_id)

    student_ids = [m.student_id for m in memberships]
    if not student_ids:
        return []

    progress_map = _progress_by_student(Enrollment, student_ids)
    pending_map, overdue_map = _submission_counts(Submission, SubmissionStatus, student_ids)

    now = timezone.now()
    rows = []
    for membership in memberships:
        student = membership.student
        progress, completed = progress_map.get(student.id, (0.0, 0))
        days_since_login = (
            (now - student.last_login).days if student.last_login else None
        )

        row = StudentRow(
            id=str(student.id),
            username=student.username,
            display_name=student.display_name,
            group_id=str(membership.group_id),
            group_name=membership.group.name,
            joined_at=membership.joined_at,
            last_login=student.last_login,
            days_since_login=days_since_login,
            progress_percent=round(progress, 1),
            completed_lessons=completed,
            pending_submissions=pending_map.get(student.id, 0),
            overdue_submissions=overdue_map.get(student.id, 0),
        )
        _evaluate_risk(row, membership_age_days=(now - membership.joined_at).days)
        rows.append(row)

    # Xavf ostidagilar tepada — mentor ularni birinchi ko'rsin
    rows.sort(key=lambda r: (not r.at_risk, r.progress_percent))
    return rows


def _progress_by_student(Enrollment, student_ids) -> dict:
    """O'quvchining eng yuqori progressli aktiv enrollment'i."""
    result: dict = {}
    enrollments = Enrollment.objects.filter(
        user_id__in=student_ids, status="active",
    ).values("user_id", "progress_percent", "completed_lessons_count")

    for row in enrollments:
        current = result.get(row["user_id"], (0.0, 0))
        candidate = (row["progress_percent"], row["completed_lessons_count"])
        if candidate[0] >= current[0]:
            result[row["user_id"]] = candidate
    return result


def _submission_counts(Submission, SubmissionStatus, student_ids) -> tuple[dict, dict]:
    from django.db.models import Count, Q

    rows = (
        Submission.objects.filter(user_id__in=student_ids)
        .exclude(status=SubmissionStatus.ACCEPTED)
        .values("user_id")
        .annotate(
            pending=Count("id"),
            overdue=Count("id", filter=Q(is_late=True)),
        )
    )
    pending = {r["user_id"]: r["pending"] for r in rows}
    overdue = {r["user_id"]: r["overdue"] for r in rows}
    return pending, overdue


def _evaluate_risk(row: StudentRow, *, membership_age_days: int) -> None:
    """Xavf mezonlari — sabablari bilan, mentor nima qilishni bilishi uchun."""
    reasons = []

    if row.last_login is None:
        reasons.append("Hech qachon tizimga kirmagan")
    elif row.days_since_login is not None and row.days_since_login >= INACTIVE_DAYS:
        reasons.append(f"{row.days_since_login} kundan beri kirmagan")

    # Yangi qo'shilgan o'quvchini past progress uchun ayblamaymiz
    if membership_age_days >= GRACE_DAYS and row.progress_percent < LOW_PROGRESS_PERCENT:
        reasons.append(f"Progress past ({row.progress_percent:.0f}%)")

    if row.overdue_submissions:
        reasons.append(f"{row.overdue_submissions} ta kechikkan topshiriq")

    row.risk_reasons = reasons
    row.at_risk = bool(reasons)
