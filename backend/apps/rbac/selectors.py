from apps.rbac.models import RoleAssignment, ScopeType


def user_has_permission(user, codename: str, scope_type: str = ScopeType.GLOBAL, scope_id=None) -> bool:
    """
    R-05: huquq tekshiruvi. Global scope'dagi rol har qanday obyektga
    ruxsat beradi; scope-bog'liq rol faqat mos scope_id uchun ishlaydi.
    """
    if user.is_superuser:
        return True

    assignments = RoleAssignment.objects.filter(
        user=user, role__permissions__codename=codename,
    ).select_related("role")

    for assignment in assignments:
        if assignment.scope_type == ScopeType.GLOBAL:
            return True
        if assignment.scope_type == scope_type and (
            scope_id is None or str(assignment.scope_id) == str(scope_id)
        ):
            return True
    return False


def get_user_role_codenames(user) -> list[str]:
    return list(
        RoleAssignment.objects.filter(user=user).values_list("role__codename", flat=True).distinct(),
    )


def get_scoped_object_ids(user, codename: str, scope_type: str) -> list | None:
    """
    Queryset darajasidagi avtomatik filtrlash uchun (R-05): berilgan huquq
    global bo'lsa None qaytaradi (cheklovsiz), aks holda ruxsat berilgan
    scope_id'lar ro'yxatini qaytaradi (masalan mentor biriktirilgan kurslar).
    """
    assignments = RoleAssignment.objects.filter(
        user=user, role__permissions__codename=codename,
    )
    if assignments.filter(scope_type=ScopeType.GLOBAL).exists():
        return None
    return list(
        assignments.filter(scope_type=scope_type).values_list("scope_id", flat=True),
    )
