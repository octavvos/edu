"""
Boshlang'ich rollar va huquqlarni yaratadi. `python manage.py seed_rbac`
bilan ishga tushiriladi (idempotent — qayta ishga tushirish xavfsiz).

Tizimda 3 ta rol bor:

  1. manager — kurs ochadi, dars vaqtlarini belgilaydi, guruh yaratadi va
     guruhga mentor biriktiradi.
  2. mentor  — o'z guruhlariga kelgan ro'yxatdan o'tish so'rovlarini
     tasdiqlaydi/rad etadi va o'quvchilarni guruhlar orasida ko'chiradi.
  3. student — ro'yxatdan o'tib, mentor tasdig'idan keyin o'z guruhining
     kursini ko'radi.

Autentifikatsiyadan o'tmagan foydalanuvchi hech qanday kursni ko'ra olmaydi
(rol ham berilmaydi) — u faqat login/register sahifasini ko'radi.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rbac.models import Permission, Role

PERMISSIONS = [
    # --- Kurs va kontent ---
    ("course.view", "Kursni ko'rish"),
    ("course.create", "Kurs ochish"),
    ("course.edit", "Kursni tahrirlash"),
    ("course.publish", "Kursni nashr qilish"),
    ("lesson.schedule", "Dars vaqtlarini belgilash"),
    ("content.manage", "Dars materiallarini yuklash va testlar yaratish"),
    # --- Guruhlar ---
    ("group.create", "Guruh yaratish"),
    ("group.edit", "Guruhni tahrirlash"),
    ("group.assign_mentor", "Guruhga mentor biriktirish"),
    ("group.view_own", "O'z guruhlarini ko'rish"),
    # --- O'quvchilar ---
    ("student.approve", "Ro'yxatdan o'tish so'rovini tasdiqlash"),
    ("student.transfer", "O'quvchini boshqa guruhga ko'chirish"),
    ("student.remove", "O'quvchini guruhdan chiqarish"),
    # --- O'quv jarayoni ---
    ("assignment.submit", "Uy vazifasi topshirish"),
    ("assignment.grade", "Uy vazifasiga baho qo'yish"),
    ("report.view", "Hisobotlarni ko'rish"),
]

ROLES = {
    "manager": {
        "name": {"uz": "Manager", "ru": "Менеджер"},
        "permissions": [
            "course.view", "course.create", "course.edit", "course.publish",
            "lesson.schedule",
            "group.create", "group.edit", "group.assign_mentor", "group.view_own",
            "report.view",
        ],
    },
    "mentor": {
        "name": {"uz": "Mentor", "ru": "Ментор"},
        "permissions": [
            "course.view",
            "group.view_own",
            "student.approve", "student.transfer", "student.remove",
            "assignment.grade",
            "content.manage",
            "report.view",
        ],
    },
    "student": {
        "name": {"uz": "O'quvchi", "ru": "Ученик"},
        "permissions": ["course.view", "assignment.submit"],
    },
}


class Command(BaseCommand):
    help = "RBAC boshlang'ich rol va huquqlarni seed qiladi (3 ta rol)"

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
                defaults={"name": data["name"], "is_system": True},
            )
            role.permissions.set(Permission.objects.filter(codename__in=data["permissions"]))

        # Eskirgan rollarni olib tashlaymiz (avvalgi 6 rolli sxemadan qolgan)
        removed, _ = Role.objects.exclude(codename__in=ROLES).delete()
        if removed:
            self.stdout.write(self.style.WARNING(f"{removed} ta eskirgan rol o'chirildi"))

        self.stdout.write(self.style.SUCCESS(f"{len(ROLES)} ta rol tayyor: {', '.join(ROLES)}"))
