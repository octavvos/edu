from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.analytics.models import DailyAggregate, Event


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ("event_type", "user", "created_at")
    list_filter = ("event_type",)

    def has_add_permission(self, request):
        return False


@admin.register(DailyAggregate)
class DailyAggregateAdmin(ModelAdmin):
    list_display = ("date", "metric", "value")
    list_filter = ("metric",)

    def has_add_permission(self, request):
        return False
