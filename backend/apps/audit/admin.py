from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.audit.models import AuditLog, ImpersonationSession


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "object_id", "ip_address")
    list_filter = ("action", "object_type")
    search_fields = ("object_id", "actor__phone", "actor__email")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ImpersonationSession)
class ImpersonationSessionAdmin(ModelAdmin):
    list_display = ("admin", "target_user", "started_at", "ended_at")
    readonly_fields = ("started_at",)
