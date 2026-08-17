from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.assignments.models import Grade, Homework, Submission


@admin.register(Homework)
class HomeworkAdmin(ModelAdmin):
    list_display = ("lesson", "deadline_at", "max_score")


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = ("user", "homework", "mentor", "status", "is_late", "submitted_at")
    list_filter = ("status", "is_late")
    search_fields = ("user__phone", "user__email")


@admin.register(Grade)
class GradeAdmin(ModelAdmin):
    list_display = ("submission", "mentor", "score", "graded_at")

    def has_add_permission(self, request):
        return False
