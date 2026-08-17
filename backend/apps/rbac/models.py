"""
Granular RBAC — TZ 3.1-3.3 (R01-R05), 5.5.1 (D-03).

6 ta boshlang'ich rol (3.1-band) shu modeldan seed qilinadi
(apps/rbac/fixtures/roles.json yoki management command orqali), lekin
kod darajasida qattiq belgilanmagan — admin panelidan yangi rol qo'shish
kod o'zgartirishsiz ishlaydi (D-03).
"""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, i18n_field


class Permission(BaseModel):
    """
    Masalan: course.publish, payment.refund, assignment.grade (R-01).
    Kod ichida `apps/<name>/permissions.py` da constant sifatida e'lon
    qilinadi va migratsiya/fixture orqali shu jadvalga seed qilinadi.
    """

    codename = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "rbac_permission"
        ordering = ["codename"]

    def __str__(self):
        return self.codename


class Role(BaseModel):
    """MVP'dagi 6 ta rol: guest, student, teacher, mentor, admin, super_admin (3.1)."""

    codename = models.SlugField(max_length=50, unique=True)
    name = i18n_field()
    is_system = models.BooleanField(
        default=False, help_text="Tizim roli — o'chirib bo'lmaydi (masalan super_admin)",
    )
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)

    class Meta:
        db_table = "rbac_role"
        ordering = ["codename"]

    def __str__(self):
        return self.codename


class ScopeType(models.TextChoices):
    """R-02: har bir huquq scope'ga ega."""

    GLOBAL = "global", "Global"
    COURSE = "course", "Kurs"
    ORGANIZATION = "organization", "Tashkilot"


class RoleAssignment(BaseModel):
    """
    R-04: foydalanuvchi bir vaqtda bir nechta rolga ega bo'lishi mumkin.
    Masalan mentor faqat biriktirilgan kursda baho qo'yadi ->
    scope_type=COURSE, scope_id=<course.id>.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments",
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    scope_type = models.CharField(max_length=20, choices=ScopeType.choices, default=ScopeType.GLOBAL)
    scope_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "rbac_role_assignment"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role", "scope_type", "scope_id"], name="uniq_role_assignment",
            ),
        ]
        indexes = [models.Index(fields=["user", "scope_type", "scope_id"])]

    def __str__(self):
        return f"{self.user} -> {self.role} ({self.scope_type}:{self.scope_id or '*'})"
