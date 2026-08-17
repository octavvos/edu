from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.enrollment.models import Enrollment, LessonNote, Progress


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = ("user", "course", "access_type", "status", "progress_percent", "starts_at")
    list_filter = ("status", "access_type")
    search_fields = ("user__phone", "user__email", "course__slug")


@admin.register(Progress)
class ProgressAdmin(ModelAdmin):
    list_display = ("enrollment", "lesson", "status", "seconds_watched")
    list_filter = ("status",)


@admin.register(LessonNote)
class LessonNoteAdmin(ModelAdmin):
    list_display = ("enrollment", "lesson", "created_at")
