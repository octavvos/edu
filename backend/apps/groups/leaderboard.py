"""
Guruh reytingi — baholangan ballar yig'indisi bo'yicha o'quvchilar tartibi.

Ball qat'iy JAMLANADI (SUM), o'rtacha emas — mentor bergan har bir baho
o'quvchining umumiy hisobiga doimiy qo'shiladi va reytingdagi o'rnini
belgilaydi (ball hech qachon kamaymaydi, faqat oshadi).
"""

from dataclasses import dataclass

from django.db.models import Count, Sum


@dataclass
class LeaderboardRow:
    """Guruh reytingi jadvalidagi bitta qator."""

    rank: int
    student_id: str
    username: str
    display_name: str
    total_score: int
    graded_count: int


def get_group_leaderboard(group) -> list[LeaderboardRow]:
    from apps.assignments.models import Grade
    from apps.groups.models import GroupMembership, MembershipStatus

    memberships = (
        GroupMembership.objects.filter(group=group, status=MembershipStatus.ACTIVE)
        .select_related("student")
    )
    student_ids = [m.student_id for m in memberships]
    if not student_ids:
        return []

    score_rows = (
        Grade.objects.filter(submission__user_id__in=student_ids)
        .values("submission__user_id")
        .annotate(total=Sum("score"), graded_count=Count("id"))
    )
    score_map = {row["submission__user_id"]: row for row in score_rows}

    rows = []
    for membership in memberships:
        student = membership.student
        agg = score_map.get(student.id)
        rows.append(LeaderboardRow(
            rank=0,
            student_id=str(student.id),
            username=student.username,
            display_name=student.display_name,
            total_score=agg["total"] if agg else 0,
            graded_count=agg["graded_count"] if agg else 0,
        ))

    # Ko'p ball to'plagan tepada; teng ballda ism bo'yicha barqaror tartib.
    rows.sort(key=lambda r: (-r.total_score, r.display_name.lower()))
    for index, row in enumerate(rows, start=1):
        row.rank = index
    return rows
