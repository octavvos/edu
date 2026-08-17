from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.payments.models import LedgerEntry, Order, Payment, Promo


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("id", "user", "course", "amount", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("user__phone", "user__email", "course__slug", "id")
    actions = ["refund_orders"]

    @admin.action(description="Tanlangan buyurtmalarni qaytarish (refund)")
    def refund_orders(self, request, queryset):
        from apps.payments.services import admin_refund

        for order in queryset:
            admin_refund(actor=request.user, order=order, reason="Admin panel orqali")


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("order", "provider", "provider_txn_id", "status", "performed_at")
    list_filter = ("provider", "status")

    def has_add_permission(self, request):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(ModelAdmin):
    list_display = ("account", "debit", "credit", "ref_type", "ref_id", "teacher", "created_at")
    list_filter = ("account",)
    readonly_fields = [f.name for f in LedgerEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Promo)
class PromoAdmin(ModelAdmin):
    list_display = ("code", "discount_type", "value", "valid_from", "valid_until", "used_count")
