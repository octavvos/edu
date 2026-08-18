"""
Demo ma'lumotlar: manager, mentor hisoblari + kurs + guruhlar + dars vaqtlari.
`python manage.py seed_demo` (idempotent).

Parollar faqat lokal demo uchun — production'da ishlatilmaydi.
"""

from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.accounts.models import User, UserStatus
from apps.catalog.models import Category
from apps.courses.models import Course, CourseLevel, Lesson, LessonType, Module
from apps.core.models import StatusChoices
from apps.groups.models import Group, GroupSchedule, Weekday
from apps.rbac.services import assign_role_by_codename

DEMO_PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "Demo manager/mentor hisoblari, kurs va guruhlarni yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        manager = self._ensure_user("manager", "Aziz", "Karimov", "manager")
        mentor = self._ensure_user("mentor", "Dilnoza", "Rahimova", "mentor")

        category, _ = Category.objects.get_or_create(
            slug="dasturlash", defaults={"name": {"uz": "Dasturlash", "ru": "Программирование"}},
        )

        course = self._ensure_course(manager, category)
        self._ensure_group(course, manager, mentor, "Frontend — ertalabki", "frontend-01",
                           [(Weekday.MONDAY, time(9, 0), time(11, 0)),
                            (Weekday.WEDNESDAY, time(9, 0), time(11, 0))])
        self._ensure_group(course, manager, mentor, "Frontend — kechki", "frontend-02",
                           [(Weekday.TUESDAY, time(18, 0), time(20, 0)),
                            (Weekday.THURSDAY, time(18, 0), time(20, 0))])
        self._ensure_group(course, manager, mentor, "Frontend — shanbalik", "frontend-03",
                           [(Weekday.SATURDAY, time(10, 0), time(13, 0))])

        self.stdout.write(self.style.SUCCESS(
            f"Demo tayyor.\n"
            f"  manager / {DEMO_PASSWORD}\n"
            f"  mentor  / {DEMO_PASSWORD}\n"
            f"  3 ta guruh: frontend-01, frontend-02, frontend-03",
        ))

    def _ensure_user(self, username: str, first_name: str, last_name: str, role: str) -> User:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "status": UserStatus.ACTIVE,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password"])
        assign_role_by_codename(user=user, codename=role)
        return user

    def _ensure_course(self, author: User, category: Category) -> Course:
        course, created = Course.objects.get_or_create(
            slug="frontend-asoslari",
            defaults={
                "title": {"uz": "Frontend asoslari", "ru": "Основы Frontend"},
                "description": {"uz": "HTML, CSS va JavaScript bo'yicha to'liq kurs."},
                "author": author,
                "category": category,
                "status": StatusChoices.PUBLISHED,
                "level": CourseLevel.BEGINNER,
                "title_plain": "Frontend asoslari",
                "price": 0,
            },
        )
        if created:
            module = Module.objects.create(course=course, title={"uz": "1-modul: HTML"}, order=1)
            for i, name in enumerate(["HTML tuzilishi", "Teglar va atributlar", "Formalar"], start=1):
                Lesson.objects.create(
                    module=module, type=LessonType.TEXT, title={"uz": name}, order=i,
                    text_content={"uz": f"<p>{name} bo'yicha dars matni.</p>"},
                )
        return course

    def _ensure_group(self, course, manager, mentor, name: str, code: str, slots) -> Group:
        group, created = Group.objects.get_or_create(
            code=slugify(code),
            defaults={
                "course": course, "name": name, "mentor": mentor,
                "created_by": manager, "capacity": 25,
            },
        )
        if created:
            GroupSchedule.objects.bulk_create([
                GroupSchedule(group=group, weekday=weekday, start_time=start, end_time=end)
                for weekday, start, end in slots
            ])
        return group
