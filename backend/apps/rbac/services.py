from apps.audit.services import log_action
from apps.rbac.models import Role, RoleAssignment


def assign_role(*, actor, user, role: Role, scope_type: str = "global", scope_id=None) -> RoleAssignment:
    """R-03: rollarni admin panelidan biriktirish."""
    assignment, created = RoleAssignment.objects.get_or_create(
        user=user, role=role, scope_type=scope_type, scope_id=scope_id,
    )
    if created:
        log_action(
            actor=actor, action="rbac.assign_role", obj=assignment,
            after={"user": str(user.id), "role": role.codename, "scope_type": scope_type},
        )
    return assignment


def assign_role_by_codename(*, user, codename: str, actor=None, scope_type: str = "global",
                            scope_id=None) -> RoleAssignment | None:
    """
    Kod ichidan (masalan ro'yxatdan o'tishda) rol biriktirish uchun qulay
    o'ram. Rol seed qilinmagan bo'lsa None qaytaradi — ro'yxatdan o'tish
    jarayoni buzilmasligi uchun.
    """
    role = Role.objects.filter(codename=codename).first()
    if not role:
        return None
    return assign_role(actor=actor, user=user, role=role, scope_type=scope_type, scope_id=scope_id)


def revoke_role(*, actor, assignment: RoleAssignment) -> None:
    before = {"user": str(assignment.user_id), "role": assignment.role.codename}
    assignment.delete()
    log_action(actor=actor, action="rbac.revoke_role", obj=assignment, before=before)
