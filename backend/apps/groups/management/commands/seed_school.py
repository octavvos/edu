"""
Haqiqiy o'quv markazi ma'lumotlarini o'rnatadi: Dasturlash kursi,
mentor va DS guruhlari (dushanba/chorshanba/juma, ketma-ket 2 soatlik).

    python manage.py seed_school            # yaratadi / yangilaydi (idempotent)
    python manage.py seed_school --purge    # avval barcha eski kurs/guruh/
                                            # o'quvchi ma'lumotlarini o'chiradi

--purge faqat kontent va foydalanuvchi ma'lumotlarini tozalaydi; rollar,
huquqlar va superuser hisoblari saqlanadi.
"""

from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User, UserStatus
from apps.catalog.models import Category
from apps.core.models import StatusChoices
from apps.courses.models import Course, CourseLevel, Module
from apps.groups.models import Group, GroupSchedule, Weekday
from apps.rbac.services import assign_role_by_codename

MENTOR_USERNAME = "Anvarjon"
MENTOR_PASSWORD = "light"

MANAGER_USERNAME = "manager"
MANAGER_PASSWORD = "light"

COURSE_SLUG = "dasturlash"
COURSE_MODULES = ["Scratch", "Python", "PostgreSQL", "Django"]

# Dars kunlari — barcha guruhlar uchun bir xil
LESSON_DAYS = [Weekday.MONDAY, Weekday.WEDNESDAY, Weekday.FRIDAY]

# Guruhlar ketma-ket 2 soatlik oraliqlarda, 08:00 dan boshlab.
# Bitta mentor to'rtala guruhni birin-ketin o'qitadi.
GROUPS = [
    ("DS2606", time(8, 0), time(10, 0)),
    ("DS2605", time(10, 0), time(12, 0)),
    ("DS2603", time(12, 0), time(14, 0)),
    ("DS2608", time(14, 0), time(16, 0)),
]


class Command(BaseCommand):
    help = "Dasturlash kursi, mentor va DS guruhlarini o'rnatadi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge", action="store_true",
            help="Avval barcha kurs/guruh/o'quvchi ma'lumotlarini o'chiradi",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["purge"]:
            self._purge()

        mentor = self._ensure_user(MENTOR_USERNAME, MENTOR_PASSWORD, "mentor", "Anvarjon")
        manager = self._ensure_user(MANAGER_USERNAME, MANAGER_PASSWORD, "manager", "Manager")
        course = self._ensure_course(author=manager)
        self._ensure_groups(course, mentor, manager)

        self.stdout.write(self.style.SUCCESS(
            f"\nTayyor.\n"
            f"  Manager: {MANAGER_USERNAME} / {MANAGER_PASSWORD}\n"
            f"  Mentor:  {MENTOR_USERNAME} / {MENTOR_PASSWORD}\n"
            f"  Kurs:    Dasturlash ({', '.join(COURSE_MODULES)})\n"
            f"  Guruhlar: " + ", ".join(
                f"{code} {s:%H:%M}-{e:%H:%M}" for code, s, e in GROUPS
            ) + "\n  Kunlar:  Dushanba, Chorshanba, Juma",
        ))

    # -- Tozalash ----------------------------------------------------------

    def _purge(self):
        """
        Bog'liqlik tartibida o'chiradi: PROTECT bog'lanishlar (Course.author,
        Order.course) sababli avval bolalar, keyin ota-ona yozuvlari.
        """
        from apps.assessments.models import Attempt
        from apps.assignments.models import Submission
        from apps.certificates.models import Certificate
        from apps.enrollment.models import Enrollment
        from apps.groups.models import GroupMembership, JoinRequest
        from apps.payments.models import LedgerEntry, Order, Payment

        steps = [
            ("sertifikat", Certificate.objects.all()),
            ("topshiriq", Submission.objects.all()),
            ("test urinishi", Attempt.objects.all()),
            ("to'lov", Payment.objects.all()),
            ("buyurtma", Order.objects.all()),
            ("ledger yozuvi", LedgerEntry.objects.all()),
            ("enrollment", Enrollment.objects.all()),
            ("so'rov", JoinRequest.objects.all()),
            ("a'zolik", GroupMembership.objects.all()),
            ("guruh", Group.objects.all()),
            ("kurs", Course.objects.all()),
        ]
        for label, queryset in steps:
            count = queryset.count()
            if count:
                queryset.delete()
                self.stdout.write(f"  o'chirildi: {count} ta {label}")

        # Superuser'lardan tashqari barcha foydalanuvchilar
        users = User.objects.filter(is_superuser=False)
        count = users.count()
        if count:
            users.delete()
            self.stdout.write(f"  o'chirildi: {count} ta foydalanuvchi")

    # -- Yaratish ----------------------------------------------------------

    def _ensure_user(self, username: str, password: str, role: str, display: str) -> User:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": display,
                "full_name": display,
                "status": UserStatus.ACTIVE,
            },
        )
        user.set_password(password)
        user.status = UserStatus.ACTIVE
        user.save(update_fields=["password", "status", "updated_at"])
        assign_role_by_codename(user=user, codename=role)
        return user

    def _ensure_course(self, *, author: User) -> Course:
        category, _ = Category.objects.get_or_create(
            slug="dasturlash",
            defaults={"name": {"uz": "Dasturlash", "ru": "Программирование"}},
        )
        course, _ = Course.objects.get_or_create(
            slug=COURSE_SLUG,
            defaults={
                "title": {"uz": "Dasturlash", "ru": "Программирование"},
                "description": {
                    "uz": "Scratch'dan Django'gacha — bosqichma-bosqich dasturlash kursi.",
                },
                "author": author,
                "category": category,
                "status": StatusChoices.PUBLISHED,
                "level": CourseLevel.BEGINNER,
                "title_plain": "Dasturlash",
                "price": 0,
            },
        )

        for order, name in enumerate(COURSE_MODULES, start=1):
            Module.objects.get_or_create(
                course=course, order=order, defaults={"title": {"uz": name}},
            )
        return course

    def _ensure_groups(self, course: Course, mentor: User, manager: User):
        for code, start, end in GROUPS:
            group, _ = Group.objects.get_or_create(
                code=code.lower(),
                defaults={
                    "course": course,
                    "name": code,
                    "mentor": mentor,
                    "created_by": manager,
                    "capacity": 25,
                },
            )
            # Mentor va kursni har doim joriy holatga keltiramiz (idempotentlik)
            group.course = course
            group.mentor = mentor
            group.name = code
            group.save(update_fields=["course", "mentor", "name", "updated_at"])

            group.schedules.all().delete()
            GroupSchedule.objects.bulk_create([
                GroupSchedule(group=group, weekday=day, start_time=start, end_time=end)
                for day in LESSON_DAYS
            ])
