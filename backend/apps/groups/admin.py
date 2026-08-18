from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.groups.models import Group, GroupMembership, GroupSchedule, JoinRequest


class GroupScheduleInline(TabularInline):
    model = GroupSchedule
    extra = 1


class GroupMembershipInline(TabularInline):
    model = GroupMembership
    extra = 0
    fields = ["student", "status", "joined_at", "left_at"]
    readonly_fields = ["joined_at"]
    autocomplete_fields = ["student"]


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ["name", "code", "course", "mentor", "active_members_count", "capacity", "is_active"]
    list_filter = ["is_active", "is_open_for_registration", "course"]
    search_fields = ["name", "code"]
    autocomplete_fields = ["mentor", "created_by"]
    inlines = [GroupScheduleInline, GroupMembershipInline]


@admin.register(JoinRequest)
class JoinRequestAdmin(ModelAdmin):
    list_display = ["student", "group", "status", "created_at", "reviewed_by", "reviewed_at"]
    list_filter = ["status", "group"]
    search_fields = ["student__username", "student__first_name", "student__last_name"]
    autocomplete_fields = ["student", "group", "reviewed_by"]


@admin.register(GroupMembership)
class GroupMembershipAdmin(ModelAdmin):
    list_display = ["student", "group", "status", "joined_at", "left_at"]
    list_filter = ["status", "group"]
    search_fields = ["student__username"]
    autocomplete_fields = ["student", "group"]
