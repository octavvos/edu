from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.communication.models import Comment, HelpfulVote


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("lesson", "user", "is_question", "status", "helpful_count", "created_at")
    list_filter = ("status", "is_question")
    search_fields = ("text", "user__phone", "user__email")
    actions = ["approve_comments", "hide_comments"]

    @admin.action(description="Tanlangan izohlarni tasdiqlash")
    def approve_comments(self, request, queryset):
        from apps.communication.services import moderate_comment

        for comment in queryset:
            moderate_comment(actor=request.user, comment=comment, approve=True)

    @admin.action(description="Tanlangan izohlarni yashirish")
    def hide_comments(self, request, queryset):
        from apps.communication.services import moderate_comment

        for comment in queryset:
            moderate_comment(actor=request.user, comment=comment, approve=False)


@admin.register(HelpfulVote)
class HelpfulVoteAdmin(ModelAdmin):
    list_display = ("comment", "user", "created_at")
