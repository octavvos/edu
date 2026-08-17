"""
Boshlang'ich rollar va huquqlarni yaratadi (TZ 3.1 — 6 ta rol,
3.2-3.3 — huquqlar matritsasi). `python manage.py seed_rbac` bilan ishga
tushiriladi (idempotent — qayta ishga tushirish xavfsiz).

Eslatma: Mehmon (guest) autentifikatsiyalanmagan foydalanuvchi bo'lgani
uchun Role jadvalida qatorga ega emas.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rbac.models import Permission, Role

PERMISSIONS = [
    ("course.view", "Kursni ko'rish"),
    ("course.create", "Kurs yaratish"),
    ("course.edit_own", "O'z kursini tahrirlash"),
    ("course.publish", "Kursni nashr qilish"),
    ("course.moderate", "Kurslarni moderatsiya qilish"),
    ("course.manage_any", "Har qanday kursni boshqarish"),
    ("assignment.submit", "Uy vazifasi topshirish"),
    ("assignment.grade", "Uy vazifasiga baho qo'yish"),
    ("payment.view_own", "O'z to'lovlarini ko'rish"),
    ("payment.view_any", "Barcha to'lovlarni ko'rish"),
    ("payment.refund", "Qaytarish (refund) qilish"),
    ("payout.request", "Payout so'rash"),
    ("payout.approve", "Payout'ni tasdiqlash"),
    ("user.block", "Foydalanuvchini bloklash"),
    ("user.impersonate", "Foydalanuvchi nomidan kirish"),
    ("role.assign", "Rol tayinlash"),
    ("audit.view", "Audit-logni ko'rish"),
    ("report.view", "Hisobotlarni ko'rish"),
    ("content.manage", "Statik kontentni boshqarish"),
    ("settings.manage", "Tizim sozlamalarini boshqarish"),
]

ROLES = {
    "student": {
        "name": {"uz": "O'quvchi", "ru": "Студент"},
        "permissions": ["course.view", "assignment.submit", "payment.view_own"],
    },
    "teacher": {
        "name": {"uz": "O'qituvchi", "ru": "Преподаватель"},
        "permissions": [
            "course.view", "course.create", "course.edit_own",
            "assignment.grade", "payment.view_own", "payout.request",
        ],
    },
    "mentor": {
        "name": {"uz": "Mentor", "ru": "Ментор"},
        "permissions": ["course.view", "assignment.grade"],
    },
    "admin": {
        "name": {"uz": "Administrator", "ru": "Администратор"},
        "permissions": [c for c, _ in PERMISSIONS if c not in ("role.assign", "settings.manage")],
    },
    "super_admin": {
        "name": {"uz": "Super-admin", "ru": "Супер-админ"},
        "permissions": [c for c, _ in PERMISSIONS],
    },
}


class Command(BaseCommand):
    help = "RBAC boshlang'ich rol va huquqlarni seed qiladi"

    @transaction.atomic
    def handle(self, *args, **options):
        for codename, description in PERMISSIONS:
            Permission.objects.update_or_create(
                codename=codename, defaults={"description": description},
            )
        self.stdout.write(self.style.SUCCESS(f"{len(PERMISSIONS)} ta huquq tayyor"))

        for codename, data in ROLES.items():
            role, _ = Role.objects.update_or_create(
                codename=codename,
                defaults={"name": data["name"], "is_system": codename == "super_admin"},
            )
            perms = Permission.objects.filter(codename__in=data["permissions"])
            role.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS(f"{len(ROLES)} ta rol tayyor"))
