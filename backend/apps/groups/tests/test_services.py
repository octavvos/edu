"""Uchta rol oqimining asosiy qoidalari."""

import pytest

from apps.accounts.models import UserStatus
from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.core.exceptions import DomainError
from apps.enrollment.models import Enrollment
from apps.groups import services
from apps.groups.models import JoinRequestStatus, MembershipStatus
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def test_approve_activates_student_and_enrolls_into_course():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = PendingUserFactory()

    request = services.create_join_request(student=student, group=group)
    assert request.status == JoinRequestStatus.PENDING

    membership = services.approve_join_request(request_obj=request, mentor=mentor)

    student.refresh_from_db()
    request.refresh_from_db()
    assert membership.status == MembershipStatus.ACTIVE
    assert request.status == JoinRequestStatus.APPROVED
    assert student.status == UserStatus.ACTIVE
    # D-07: event orqali enrollment ochilgan bo'lishi kerak
    assert Enrollment.objects.filter(user=student, course=group.course).exists()


def test_mentor_cannot_approve_request_for_another_mentors_group():
    group = GroupFactory(mentor=UserFactory())
    outsider = UserFactory()
    request = services.create_join_request(student=PendingUserFactory(), group=group)

    with pytest.raises(DomainError) as exc:
        services.approve_join_request(request_obj=request, mentor=outsider)
    assert exc.value.status_code == 403


def test_reject_keeps_student_pending():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor)
    student = PendingUserFactory()
    request = services.create_join_request(student=student, group=group)

    services.reject_join_request(request_obj=request, mentor=mentor, note="Hujjat yetarli emas")

    student.refresh_from_db()
    request.refresh_from_db()
    assert request.status == JoinRequestStatus.REJECTED
    assert request.review_note == "Hujjat yetarli emas"
    # Rad etilgan o'quvchi kurslarni ko'ra olmasligi kerak
    assert student.status == UserStatus.PENDING
    assert not Enrollment.objects.filter(user=student).exists()


def test_duplicate_join_request_returns_existing_one():
    group = GroupFactory(mentor=UserFactory())
    student = PendingUserFactory()

    first = services.create_join_request(student=student, group=group)
    second = services.create_join_request(student=student, group=group)

    assert first.id == second.id


def test_approve_rejects_when_group_is_full():
    mentor = UserFactory()
    group = GroupFactory(mentor=mentor, capacity=1)
    services.approve_join_request(
        request_obj=services.create_join_request(student=PendingUserFactory(), group=group),
        mentor=mentor,
    )

    overflow = services.create_join_request(student=PendingUserFactory(), group=group)
    with pytest.raises(DomainError) as exc:
        services.approve_join_request(request_obj=overflow, mentor=mentor)
    assert exc.value.code == "group_full"


def test_transfer_moves_student_and_keeps_history():
    mentor = UserFactory()
    source = GroupFactory(mentor=mentor)
    target = GroupFactory(mentor=mentor, course=source.course)
    student = PendingUserFactory()

    services.approve_join_request(
        request_obj=services.create_join_request(student=student, group=source), mentor=mentor,
    )
    membership = services.transfer_student(
        student=student, from_group=source, to_group=target, mentor=mentor,
    )

    assert membership.group_id == target.id
    assert membership.status == MembershipStatus.ACTIVE
    # Eski a'zolik o'chirilmaydi — tarix sifatida qoladi
    old = source.memberships.get(student=student)
    assert old.status == MembershipStatus.TRANSFERRED
    assert old.left_at is not None


def test_transfer_to_another_course_enrolls_student_there_too():
    mentor = UserFactory()
    source = GroupFactory(mentor=mentor)
    target = GroupFactory(mentor=mentor)  # boshqa kurs
    student = PendingUserFactory()

    services.approve_join_request(
        request_obj=services.create_join_request(student=student, group=source), mentor=mentor,
    )
    services.transfer_student(student=student, from_group=source, to_group=target, mentor=mentor)

    assert Enrollment.objects.filter(user=student, course=target.course).exists()


def test_transfer_rejected_for_unrelated_mentor():
    owner = UserFactory()
    source = GroupFactory(mentor=owner)
    target = GroupFactory(mentor=owner)
    student = PendingUserFactory()
    services.approve_join_request(
        request_obj=services.create_join_request(student=student, group=source), mentor=owner,
    )

    with pytest.raises(DomainError) as exc:
        services.transfer_student(
            student=student, from_group=source, to_group=target, mentor=UserFactory(),
        )
    assert exc.value.status_code == 403


def test_join_request_rejected_for_closed_group():
    group = GroupFactory(mentor=UserFactory(), is_open_for_registration=False)

    with pytest.raises(DomainError) as exc:
        services.create_join_request(student=PendingUserFactory(), group=group)
    assert exc.value.code == "group_closed"
