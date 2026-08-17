from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.catalog.models import Category, Review


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("slug", "parent", "order")
    list_filter = ("parent",)
    search_fields = ("slug",)


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("course", "user", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    search_fields = ("course__slug", "user__phone", "user__email")
    actions = ["approve_reviews", "reject_reviews"]

    @admin.action(description="Tanlangan sharhlarni tasdiqlash")
    def approve_reviews(self, request, queryset):
        from apps.catalog.services import moderate_review

        for review in queryset:
            moderate_review(actor=request.user, review=review, approve=True)

    @admin.action(description="Tanlangan sharhlarni rad etish")
    def reject_reviews(self, request, queryset):
        from apps.catalog.services import moderate_review

        for review in queryset:
            moderate_review(actor=request.user, review=review, approve=False)
