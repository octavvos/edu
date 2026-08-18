"""DRF permission klasslari — RBAC huquqlari va rollar ustida ishlaydi."""

from rest_framework.permissions import BasePermission

from apps.rbac.selectors import get_user_role_codenames, user_has_permission


class HasPermission(BasePermission):
    """
    View'da `required_permission = "group.create"` deb belgilanadi.
    Superuser har doim o'tadi (rbac.selectors ichida hisobga olingan).
    """

    message = "Bu amalni bajarishga huquqingiz yo'q."

    def has_permission(self, request, view):
        codename = getattr(view, "required_permission", None)
        if not codename:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return user_has_permission(request.user, codename)


class HasRole(BasePermission):
    """View'da `required_roles = ("mentor",)` deb belgilanadi."""

    message = "Bu bo'lim sizning rolingiz uchun mo'ljallanmagan."

    def has_permission(self, request, view):
        required = getattr(view, "required_roles", None)
        if not required:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return bool(set(required) & set(get_user_role_codenames(user)))


class IsApprovedStudent(BasePermission):
    """
    O'quvchi mentor tomonidan guruhga qabul qilinmaguncha kurs kontentiga
    kira olmaydi (status=pending).
    """

    message = "Mentor sizni guruhga qabul qilishini kuting."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return not user.is_pending_approval
