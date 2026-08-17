from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.certificates.models import Certificate, CertificateTemplate


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(ModelAdmin):
    list_display = ("name", "is_default")


@admin.register(Certificate)
class CertificateAdmin(ModelAdmin):
    list_display = ("code", "user", "course", "issued_at")
    search_fields = ("code", "user__phone", "user__email", "course__slug")

    def has_add_permission(self, request):
        return False
