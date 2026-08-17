from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.payouts.models import PayoutRequest


@admin.register(PayoutRequest)
class PayoutRequestAdmin(ModelAdmin):
    list_display = ("teacher", "amount", "status", "created_at", "processed_at")
    list_filter = ("status",)
    search_fields = ("teacher__phone", "teacher__email")
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Tanlangan so'rovlarni tasdiqlash va to'lash")
    def approve_selected(self, request, queryset):
        from apps.payouts.services import approve_payout

        for payout in queryset:
            approve_payout(actor=request.user, payout=payout)

    @admin.action(description="Tanlangan so'rovlarni rad etish")
    def reject_selected(self, request, queryset):
        from apps.payouts.services import reject_payout

        for payout in queryset:
            reject_payout(actor=request.user, payout=payout)
