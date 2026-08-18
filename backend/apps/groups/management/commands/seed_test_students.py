"""
Sinov uchun soxta o'quvchilar yaratadi — har bir guruhga bir nechtadan.

    python manage.py seed_test_students             # har guruhga 10 tadan
    python manage.py seed_test_students --per-group 5
    python manage.py seed_test_students --purge     # faqat sinov o'quvchilarini o'chiradi

O'quvchilar haqiqiy oqim orqali qo'shiladi (so'rov -> mentor tasdig'i), shuning
uchun ular kursga ham yoziladi va vazifa/reyting/davomat bo'limlarida
to'g'ri ko'rinadi.

Username qat'iy `test<raqam>` ko'rinishida (test1, test2, ...) — `--purge`
aynan shu naqsh bo'yicha o'chiradi, shuning uchun boshqa hisoblar
(masalan qo'lda yaratilgan `test`) tegilmaydi.
"""

import re

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User, UserStatus
from apps.groups import services as group_services
from apps.groups.models import Group, MembershipStatus
from apps.rbac.services import assign_role_by_codename

# Sinov hisoblarini aniqlash naqshi — `test` (raqamsiz) bunga tushmaydi.
TEST_USERNAME_RE = re.compile(r"^test\d+$")
TEST_USERNAME_SQL = r"^test[0-9]+$"

DEFAULT_PASSWORD = "light"
DEFAULT_PER_GROUP = 10

FIRST_NAMES = [
    "Aziza", "Bekzod", "Dilnoza", "Eldor", "Feruza",
    "G'ayrat", "Hulkar", "Islom", "Jasur", "Kamola",
    "Laziz", "Madina", "Nodir", "Ozoda", "Rustam",
    "Sevara", "Temur", "Umida", "Vohid", "Yulduz",
    "Zafar", "Malika", "Sardor", "Nilufar", "Otabek",
    "Gulnora", "Sherzod", "Zilola", "Farrux", "Mohira",
    "Doniyor", "Sabina", "Alisher", "Nargiza", "Bobur",
    "Dilfuza", "Javohir", "Shahnoza", "Ravshan", "Kamila",
]

LAST_NAMES = [
    "Karimova", "Rahimov", "Yusupova", "Toshev", "Ergasheva",
    "Sobirov", "Nazarova", "Qodirov", "Aliyev", "Xolmatova",
    "Sultonov", "Ibrohimova", "Tursunov", "Mirzayeva", "Saidov",
    "Yo'ldosheva", "Abdullayev", "Hamidova", "Nurmatov", "Ismoilova",
]


class Command(BaseCommand):
    help = "Har bir guruhga sinov o'quvchilarini qo'shadi (test1, test2, ...)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-group", type=int, default=DEFAULT_PER_GROUP,
            help=f"Har bir guruhga nechtadan (standart: {DEFAULT_PER_GROUP})",
        )
        parser.add_argument(
            "--password", default=DEFAULT_PASSWORD,
            help=f"Barcha sinov hisoblari uchun parol (standart: {DEFAULT_PASSWORD})",
        )
        parser.add_argument(
            "--purge", action="store_true",
            help="Sinov o'quvchilarini o'chiradi va hech kimni yaratmaydi",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["purge"]:
            self._purge()
            return

        groups = list(Group.objects.filter(is_active=True).order_by("name"))
        if not groups:
            self.stdout.write(self.style.ERROR(
                "Faol guruh topilmadi — avval `seed_school` ni ishga tushiring.",
            ))
            return

        per_group = options["per_group"]
        password = options["password"]
        counter = 0
        created_total = 0

        for group in groups:
            if not group.mentor:
                self.stdout.write(self.style.WARNING(
                    f"  {group.name}: mentor biriktirilmagan — o'tkazib yuborildi",
                ))
                continue

            added = 0
            for _ in range(per_group):
                counter += 1
                username = f"test{counter}"
                user, created = self._ensure_student(username, password, counter)
                if self._admit(user, group):
                    added += 1
                if created:
                    created_total += 1

            self.stdout.write(f"  {group.name}: {added} ta o'quvchi ({group.active_members_count} ta a'zo)")

        self.stdout.write(self.style.SUCCESS(
            f"\nTayyor: {created_total} ta yangi hisob yaratildi, parol — {password}\n"
            f"Username'lar: test1 … test{counter}\n"
            f"O'chirish: python manage.py seed_test_students --purge",
        ))

    # -- Yaratish ----------------------------------------------------------

    def _ensure_student(self, username: str, password: str, index: int) -> tuple[User, bool]:
        first = FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]
        last = LAST_NAMES[(index - 1) % len(LAST_NAMES)]
        display = f"{first} {last}"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first,
                "last_name": last,
                "full_name": display,
                "status": UserStatus.ACTIVE,
            },
        )
        user.set_password(password)
        user.status = UserStatus.ACTIVE
        user.save(update_fields=["password", "status", "updated_at"])
        assign_role_by_codename(user=user, codename="student")
        return user, created

    def _admit(self, student: User, group: Group) -> bool:
        """Haqiqiy oqim: so'rov -> mentor tasdig'i (kursga yozilish shu yerda bo'ladi)."""
        already = group.memberships.filter(
            student=student, status=MembershipStatus.ACTIVE,
        ).exists()
        if already:
            return False

        request_obj = group_services.create_join_request(student=student, group=group)
        group_services.approve_join_request(request_obj=request_obj, mentor=group.mentor)
        return True

    # -- Tozalash ----------------------------------------------------------

    def _purge(self):
        """
        Faqat `test<raqam>` hisoblarini o'chiradi. Ular bilan bog'liq
        a'zolik, so'rov, enrollment, topshiriq, davomat yozuvlari
        CASCADE orqali o'zi o'chadi.
        """
        students = User.objects.filter(
            username__regex=TEST_USERNAME_SQL, is_superuser=False,
        )
        # Ehtiyot chorasi: naqshga tushmagan hech narsa o'chmasin.
        usernames = [u.username for u in students]
        unexpected = [name for name in usernames if not TEST_USERNAME_RE.match(name)]
        if unexpected:
            self.stdout.write(self.style.ERROR(
                f"To'xtatildi — kutilmagan username'lar: {', '.join(unexpected)}",
            ))
            return

        if not usernames:
            self.stdout.write("Sinov o'quvchisi topilmadi — o'chiriladigan narsa yo'q.")
            return

        students.delete()
        self.stdout.write(self.style.SUCCESS(
            f"O'chirildi: {len(usernames)} ta sinov o'quvchisi "
            f"({usernames[0]} … {usernames[-1]})",
        ))
