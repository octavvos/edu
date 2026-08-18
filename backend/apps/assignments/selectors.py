from django.db.models import Q
from django.utils import timezone

from apps.assignments.models import Homework, Submission, SubmissionStatus


def get_mentor_queue(mentor, *, status: str = "", group_id=None):
    """
    Mentor kabineti — tekshirilishi kerak bo'lgan topshiriqlar.

    Mentor o'ziga biriktirilgan topshiriqlarni va o'z guruhlaridagi
    o'quvchilarning hali biriktirilmagan topshiriqlarini ko'radi (masalan
    o'quvchi guruhga mentor tayinlanishidan oldin topshirgan bo'lsa).
    """
    from apps.groups.models import MembershipStatus

    student_filter = Q(
        user__group_memberships__group__mentor=mentor,
        user__group_memberships__status=MembershipStatus.ACTIVE,
    )
    queryset = Submission.objects.filter(Q(mentor=mentor) | student_filter)

    if group_id:
        queryset = queryset.filter(user__group_memberships__group_id=group_id)

    if status:
        queryset = queryset.filter(status=status)
    else:
        # Standart holatda yakunlangan topshiriqlar navbatni to'ldirmasin
        queryset = queryset.exclude(status=SubmissionStatus.ACCEPTED)

    return (
        queryset.select_related("user", "grade", "homework", "homework__lesson")
        .distinct()
        .order_by("-is_late", "submitted_at")
    )


def get_mentor_queue_counts(mentor) -> dict:
    """Holatlar bo'yicha sanoq — mentor panelidagi filtr tugmalari uchun."""
    from django.db.models import Count

    # Barcha holatlarni (shu jumladan "qabul qilindi") sanaymiz, shuning
    # uchun statusni alohida ko'rsatib, standart exclude'ni chetlab o'tamiz.
    rows = (
        Submission.objects.filter(
            id__in=_mentor_submission_ids(mentor),
        )
        .values("status")
        .annotate(count=Count("id"))
    )
    counts = {row["status"]: row["count"] for row in rows}
    counts["late"] = (
        Submission.objects.filter(id__in=_mentor_submission_ids(mentor), is_late=True)
        .exclude(status=SubmissionStatus.ACCEPTED)
        .count()
    )
    return counts


def _mentor_submission_ids(mentor):
    from apps.groups.models import MembershipStatus

    return Submission.objects.filter(
        Q(mentor=mentor)
        | Q(
            user__group_memberships__group__mentor=mentor,
            user__group_memberships__status=MembershipStatus.ACTIVE,
        ),
    ).values_list("id", flat=True).distinct()


def get_gradebook(course):
    """H-06: baholar jurnali — CSV/XLSX eksport uchun manba."""
    return (
        Submission.objects.filter(homework__lesson__module__course=course)
        .select_related("user", "homework", "grade")
        .order_by("user__last_name", "user__first_name", "homework__lesson__order")
    )


def get_user_submissions(*, user, course):
    return Submission.objects.filter(
        user=user, homework__lesson__module__course=course,
    ).select_related("homework", "grade")


def get_my_assignments(user):
    """
    O'quvchiga mentor jo'natgan vazifalar — faqat o'z guruhiga
    jo'natilganlari. Har bir Homework'ga o'quvchining o'z Submission'i
    (mavjud bo'lsa, `grade` bilan) `_my_submission` sifatida biriktiriladi —
    `MyAssignmentSerializer` shundan foydalanadi.
    """
    from apps.groups.selectors import get_active_membership

    membership = get_active_membership(user)
    if not membership:
        return []

    homeworks = list(
        Homework.objects.filter(group=membership.group)
        .select_related("lesson", "lesson__module", "material")
        .order_by("-created_at"),
    )
    submissions = {
        s.homework_id: s
        for s in Submission.objects.filter(
            user=user, homework_id__in=[hw.id for hw in homeworks],
        ).select_related("grade")
    }
    for hw in homeworks:
        hw._my_submission = submissions.get(hw.id)
    return homeworks


def count_overdue_for(user) -> int:
    """Deadline'i o'tgan, lekin hali qabul qilinmagan topshiriqlar soni."""
    return Submission.objects.filter(
        user=user, is_late=True,
    ).exclude(status=SubmissionStatus.ACCEPTED).count()


def count_pending_review_for(mentor) -> int:
    return get_mentor_queue(mentor).count()


def has_missed_deadline(user) -> bool:
    """O'z guruhiga jo'natilgan, topshirilmagan va muddati o'tgan vazifa bormi."""
    from apps.groups.selectors import get_active_membership

    membership = get_active_membership(user)
    if not membership:
        return False

    now = timezone.now()
    submitted_ids = Submission.objects.filter(user=user).values_list("homework_id", flat=True)
    return Homework.objects.filter(
        deadline_at__lt=now, group=membership.group,
    ).exclude(id__in=submitted_ids).exists()
