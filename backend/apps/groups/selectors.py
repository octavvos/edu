"""Faqat o'qish operatsiyalari (TZ 5.1)."""

from apps.groups.models import (
    Group,
    GroupMembership,
    JoinRequest,
    JoinRequestStatus,
    MembershipStatus,
)


def get_open_groups():
    """Ro'yxatdan o'tish formasida ko'rsatiladigan guruhlar (autentifikatsiyasiz)."""
    return (
        Group.objects.filter(is_active=True, is_open_for_registration=True)
        .select_related("course")
        .prefetch_related("schedules")
        .order_by("name")
    )


def get_group_by_code(code: str) -> Group | None:
    return Group.objects.filter(code=code, is_active=True).first()


def get_mentor_groups(mentor):
    return (
        Group.objects.filter(mentor=mentor, is_active=True)
        .select_related("course")
        .prefetch_related("schedules")
        .order_by("name")
    )


def get_pending_requests_for_mentor(mentor):
    """Mentor tasdiqlashi kerak bo'lgan so'rovlar — faqat o'z guruhlari bo'yicha."""
    return (
        JoinRequest.objects.filter(group__mentor=mentor, status=JoinRequestStatus.PENDING)
        .select_related("student", "group", "group__course")
        .order_by("created_at")
    )


def get_group_members(group):
    return (
        GroupMembership.objects.filter(group=group, status=MembershipStatus.ACTIVE)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )


def get_active_membership(student) -> GroupMembership | None:
    return (
        GroupMembership.objects.filter(student=student, status=MembershipStatus.ACTIVE)
        .select_related("group", "group__course", "group__mentor")
        .first()
    )


def get_student_groups(student):
    return (
        Group.objects.filter(
            memberships__student=student, memberships__status=MembershipStatus.ACTIVE,
        )
        .select_related("course")
        .prefetch_related("schedules")
        .distinct()
    )


def get_latest_join_request(student) -> JoinRequest | None:
    return (
        JoinRequest.objects.filter(student=student)
        .select_related("group", "group__course")
        .order_by("-created_at")
        .first()
    )
