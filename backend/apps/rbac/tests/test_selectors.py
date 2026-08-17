import pytest

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory
from apps.rbac.models import Permission, Role, ScopeType
from apps.rbac.selectors import user_has_permission
from apps.rbac.services import assign_role

pytestmark = pytest.mark.django_db


def test_global_role_grants_permission_everywhere():
    user = UserFactory()
    perm = Permission.objects.create(codename="course.publish")
    role = Role.objects.create(codename="admin", name={"uz": "Admin"})
    role.permissions.add(perm)

    assign_role(actor=user, user=user, role=role, scope_type=ScopeType.GLOBAL)

    assert user_has_permission(user, "course.publish") is True
    assert user_has_permission(user, "course.publish", scope_type=ScopeType.COURSE, scope_id="anything") is True


def test_course_scoped_role_only_grants_for_matching_course():
    user = UserFactory()
    course = CourseFactory()
    other_course = CourseFactory()
    perm = Permission.objects.create(codename="assignment.grade")
    role = Role.objects.create(codename="mentor", name={"uz": "Mentor"})
    role.permissions.add(perm)

    assign_role(actor=user, user=user, role=role, scope_type=ScopeType.COURSE, scope_id=course.id)

    assert user_has_permission(user, "assignment.grade", scope_type=ScopeType.COURSE, scope_id=course.id) is True
    assert user_has_permission(user, "assignment.grade", scope_type=ScopeType.COURSE, scope_id=other_course.id) is False


def test_no_role_means_no_permission():
    user = UserFactory()
    Permission.objects.create(codename="payment.refund")

    assert user_has_permission(user, "payment.refund") is False
