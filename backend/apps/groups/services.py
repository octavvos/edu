"""
Guruh domenidagi barcha yozish operatsiyalari (TZ 5.1 — view'da logika yo'q).

Manager: guruh yaratish/tahrirlash, dars vaqtlari, mentor biriktirish.
Mentor:  so'rovni tasdiqlash/rad etish, o'quvchini boshqa guruhga ko'chirish.
"""

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserStatus
from apps.core.events import EVENT_STUDENT_ADMITTED, EVENT_STUDENT_TRANSFERRED, publish
from apps.core.exceptions import DomainError
from apps.groups.models import (
    Attendance,
    AttendanceStatus,
    Group,
    GroupMembership,
    GroupSchedule,
    JoinRequest,
    JoinRequestStatus,
    MembershipStatus,
)


class GroupError(DomainError):
    pass


# ---------------------------------------------------------------------------
# Manager operatsiyalari
# ---------------------------------------------------------------------------

@transaction.atomic
def create_group(*, course, name: str, code: str, manager, mentor=None, capacity: int = 30,
                 starts_on=None, ends_on=None) -> Group:
    if Group.objects.filter(code=code).exists():
        raise GroupError("Bu kod bilan guruh allaqachon mavjud", code="group_code_taken")
    return Group.objects.create(
        course=course, name=name, code=code, created_by=manager, mentor=mentor,
        capacity=capacity, starts_on=starts_on, ends_on=ends_on,
    )


@transaction.atomic
def assign_mentor(*, group: Group, mentor) -> Group:
    group.mentor = mentor
    group.save(update_fields=["mentor", "updated_at"])
    return group


@transaction.atomic
def set_schedule(*, group: Group, slots: list[dict]) -> list[GroupSchedule]:
    """
    Dars vaqtlarini to'liq almashtiradi (manager formadagi jadvalni yuboradi).
    slots: [{"weekday": 1, "start_time": "18:00", "end_time": "20:00", "room": "..."}]
    """
    for slot in slots:
        if slot["end_time"] <= slot["start_time"]:
            raise GroupError("Dars tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak",
                             code="invalid_time_range")

    group.schedules.all().delete()
    return GroupSchedule.objects.bulk_create([
        GroupSchedule(
            group=group,
            weekday=slot["weekday"],
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            room=slot.get("room", ""),
            online_url=slot.get("online_url", ""),
        )
        for slot in slots
    ])


# ---------------------------------------------------------------------------
# O'quvchi: ro'yxatdan o'tishda so'rov yaratish
# ---------------------------------------------------------------------------

@transaction.atomic
def create_join_request(*, student, group: Group) -> JoinRequest:
    if not group.is_active or not group.is_open_for_registration:
        raise GroupError("Bu guruhga hozir ro'yxatdan o'tish yopiq", code="group_closed")

    existing = JoinRequest.objects.filter(
        student=student, group=group, status=JoinRequestStatus.PENDING,
    ).first()
    if existing:
        return existing

    return JoinRequest.objects.create(student=student, group=group)


# ---------------------------------------------------------------------------
# Mentor operatsiyalari
# ---------------------------------------------------------------------------

def _assert_mentor_owns_group(mentor, group: Group) -> None:
    if group.mentor_id != mentor.id:
        raise GroupError("Bu guruh sizga biriktirilmagan", code="not_your_group", status_code=403)


@transaction.atomic
def approve_join_request(*, request_obj: JoinRequest, mentor) -> GroupMembership:
    """Mentor so'rovni tasdiqlaydi -> a'zolik ochiladi va o'quvchi kursga yoziladi."""
    _assert_mentor_owns_group(mentor, request_obj.group)

    if request_obj.status != JoinRequestStatus.PENDING:
        raise GroupError("Bu so'rov allaqachon ko'rib chiqilgan", code="already_reviewed")

    group = request_obj.group
    if not group.has_free_seats:
        raise GroupError("Guruhda bo'sh joy qolmagan", code="group_full")

    request_obj.status = JoinRequestStatus.APPROVED
    request_obj.reviewed_by = mentor
    request_obj.reviewed_at = timezone.now()
    request_obj.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

    membership, _ = GroupMembership.objects.get_or_create(
        group=group, student=request_obj.student, status=MembershipStatus.ACTIVE,
        defaults={"added_by": mentor},
    )

    student = request_obj.student
    if student.status == UserStatus.PENDING:
        student.status = UserStatus.ACTIVE
        student.save(update_fields=["status", "updated_at"])

    publish(EVENT_STUDENT_ADMITTED, user_id=str(student.id), course_id=str(group.course_id),
            group_id=str(group.id))
    return membership


@transaction.atomic
def reject_join_request(*, request_obj: JoinRequest, mentor, note: str = "") -> JoinRequest:
    _assert_mentor_owns_group(mentor, request_obj.group)

    if request_obj.status != JoinRequestStatus.PENDING:
        raise GroupError("Bu so'rov allaqachon ko'rib chiqilgan", code="already_reviewed")

    request_obj.status = JoinRequestStatus.REJECTED
    request_obj.reviewed_by = mentor
    request_obj.reviewed_at = timezone.now()
    request_obj.review_note = note[:255]
    request_obj.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
    return request_obj


@transaction.atomic
def transfer_student(*, student, from_group: Group, to_group: Group, mentor) -> GroupMembership:
    """
    O'quvchini boshqa guruhga ko'chirish. Mentor manba yoki maqsad guruhning
    egasi bo'lishi kerak — aks holda begona guruhga o'quvchi qo'sha olardi.
    """
    if from_group.id == to_group.id:
        raise GroupError("Manba va maqsad guruh bir xil", code="same_group")
    if mentor.id not in (from_group.mentor_id, to_group.mentor_id):
        raise GroupError("Bu guruhlar sizga biriktirilmagan", code="not_your_group", status_code=403)
    if not to_group.is_active:
        raise GroupError("Maqsad guruh faol emas", code="group_inactive")
    if not to_group.has_free_seats:
        raise GroupError("Maqsad guruhda bo'sh joy qolmagan", code="group_full")

    current = GroupMembership.objects.filter(
        group=from_group, student=student, status=MembershipStatus.ACTIVE,
    ).first()
    if not current:
        raise GroupError("O'quvchi bu guruhda faol emas", code="not_a_member")

    current.status = MembershipStatus.TRANSFERRED
    current.left_at = timezone.now()
    current.save(update_fields=["status", "left_at", "updated_at"])

    membership = GroupMembership.objects.create(
        group=to_group, student=student, added_by=mentor, status=MembershipStatus.ACTIVE,
    )

    # Maqsad guruh boshqa kursga tegishli bo'lsa, o'quvchi o'sha kursga ham yoziladi
    if from_group.course_id != to_group.course_id:
        publish(EVENT_STUDENT_TRANSFERRED, user_id=str(student.id),
                course_id=str(to_group.course_id), group_id=str(to_group.id))
    return membership


@transaction.atomic
def remove_student(*, student, group: Group, mentor) -> None:
    _assert_mentor_owns_group(mentor, group)
    GroupMembership.objects.filter(
        group=group, student=student, status=MembershipStatus.ACTIVE,
    ).update(status=MembershipStatus.REMOVED, left_at=timezone.now())


# ---------------------------------------------------------------------------
# Davomat
# ---------------------------------------------------------------------------

@transaction.atomic
def mark_attendance(*, mentor, group: Group, date, records: list[dict]) -> int:
    """
    Guruhning bir kunlik davomatini belgilaydi. `records` — har biri
    `{"student_id": ..., "status": ..., "note": ...}`. Qayta belgilash
    mavjud yozuvni yangilaydi (kunlik kalit: guruh + o'quvchi + sana).

    Faqat guruhning FAOL a'zolari qabul qilinadi — chiqarilgan yoki
    boshqa guruhga ko'chirilgan o'quvchiga davomat qo'yib bo'lmaydi.
    """
    _assert_mentor_owns_group(mentor, group)

    if date > timezone.localdate():
        raise GroupError("Kelajakdagi sana uchun davomat olib bo'lmaydi", code="future_date")

    member_ids = set(
        GroupMembership.objects.filter(
            group=group, status=MembershipStatus.ACTIVE,
        ).values_list("student_id", flat=True),
    )
    valid_statuses = set(AttendanceStatus.values)

    for record in records:
        student_id = record["student_id"]
        if student_id not in member_ids:
            raise GroupError("O'quvchi bu guruhning faol a'zosi emas", code="not_a_member")
        if record["status"] not in valid_statuses:
            raise GroupError("Noto'g'ri davomat holati", code="invalid_status")

        Attendance.objects.update_or_create(
            group=group, student_id=student_id, date=date,
            defaults={
                "status": record["status"],
                "note": record.get("note", "") or "",
                "marked_by": mentor,
            },
        )
    return len(records)
