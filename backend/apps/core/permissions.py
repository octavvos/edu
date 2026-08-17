"""
Granular RBAC permission tekshiruvi — TZ 3.3 (R01-R05), 5.5 (Role/Permission).
API darajasida ishlatiladi; queryset darajasidagi filtrlash uchun
`apps/core/selectors.py` va har bir app'ning `selectors.py`siga qarang.
"""

from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """
    DRF view'da: `permission_classes = [HasPermission]`,
    `required_permission = "course.publish"` deb belgilanadi.
    Scope (global/course/organization) service qatlamida tekshiriladi,
    chunki u obyektga bog'liq (R-02).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        codename = getattr(view, "required_permission", None)
        if codename is None:
            return True
        return request.user.has_perm_scoped(codename)


class IsCourseOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.has_perm_scoped("course.manage_any"):
            return True
        return getattr(obj, "author_id", None) == user.id
