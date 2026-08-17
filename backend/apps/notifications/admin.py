from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.notifications.models import NotificationDispatch, NotificationPreference, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(ModelAdmin):
    list_display = ("event", "channel", "is_active")
    list_filter = ("channel", "is_active")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(ModelAdmin):
    list_display = ("user", "event", "channel", "enabled")
    list_filter = ("channel", "enabled")
    search_fields = ("user__phone", "user__email")


@admin.register(NotificationDispatch)
class NotificationDispatchAdmin(ModelAdmin):
    list_display = ("user", "event", "channel", "status", "attempts", "created_at")
    list_filter = ("status", "channel")
    search_fields = ("user__phone", "user__email")

    def has_add_permission(self, request):
        return False
