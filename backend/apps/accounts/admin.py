from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from unfold.admin import ModelAdmin

from apps.accounts.models import Device, LoginAttempt, User, UserSession


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    model = User
    list_display = ("phone", "email", "full_name", "status", "is_staff", "created_at")
    list_filter = ("status", "is_staff", "is_superuser", "is_phone_verified")
    search_fields = ("phone", "email", "full_name")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at", "last_login")
    fieldsets = (
        (None, {"fields": ("phone", "email", "password")}),
        ("Shaxsiy ma'lumot", {"fields": ("full_name", "avatar", "birth_date", "gender", "city")}),
        ("Sozlamalar", {"fields": ("language", "timezone", "theme")}),
        ("Holat", {"fields": ("status", "is_phone_verified", "is_email_verified", "organization_id")}),
        ("Huquqlar", {"fields": ("is_active", "is_staff", "is_superuser", "totp_enabled")}),
        ("Muhim sanalar", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone", "email", "password1", "password2")}),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    list_display = ("user", "device_id", "name", "is_active", "last_seen_at")
    list_filter = ("is_active",)
    search_fields = ("user__phone", "user__email", "device_id")


@admin.register(UserSession)
class UserSessionAdmin(ModelAdmin):
    list_display = ("user", "device", "ip_address", "created_at", "revoked_at")
    list_filter = ("revoked_at",)
    search_fields = ("user__phone", "user__email")


@admin.register(LoginAttempt)
class LoginAttemptAdmin(ModelAdmin):
    list_display = ("identifier", "success", "ip_address", "created_at", "reason")
    list_filter = ("success",)
    search_fields = ("identifier", "ip_address")

    def has_add_permission(self, request):
        return False
