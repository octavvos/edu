from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.rbac.models import Permission, Role, RoleAssignment


@admin.register(Permission)
class PermissionAdmin(ModelAdmin):
    list_display = ("codename", "description")
    search_fields = ("codename",)


class RoleAssignmentInline(TabularInline):
    model = RoleAssignment
    extra = 0
    fk_name = "role"


@admin.register(Role)
class RoleAdmin(ModelAdmin):
    list_display = ("codename", "is_system")
    filter_horizontal = ("permissions",)
    search_fields = ("codename",)
    inlines = [RoleAssignmentInline]


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(ModelAdmin):
    list_display = ("user", "role", "scope_type", "scope_id")
    list_filter = ("scope_type", "role")
    search_fields = ("user__phone", "user__email")
    autocomplete_fields = ("user", "role")
