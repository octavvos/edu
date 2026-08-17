from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.assessments.models import Answer, Attempt, Choice, Question, Quiz


class ChoiceInline(TabularInline):
    model = Choice
    extra = 2


class QuestionInline(TabularInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(ModelAdmin):
    list_display = ("lesson", "pass_percent", "max_attempts", "time_limit_seconds")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ("quiz", "type", "points", "order")
    list_filter = ("type",)
    inlines = [ChoiceInline]


@admin.register(Attempt)
class AttemptAdmin(ModelAdmin):
    list_display = ("user", "quiz", "status", "score_percent", "passed", "started_at")
    list_filter = ("status", "passed")
    search_fields = ("user__phone", "user__email")

    def has_add_permission(self, request):
        return False


@admin.register(Answer)
class AnswerAdmin(ModelAdmin):
    list_display = ("attempt", "question", "is_correct", "points_awarded")

    def has_add_permission(self, request):
        return False
