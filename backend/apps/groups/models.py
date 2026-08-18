"""
Guruhlar (bounded context: "o'quv guruhi").

Rollar taqsimoti:
  * Manager — kurs ochadi, guruh yaratadi, dars vaqtlarini belgilaydi va
    guruhga mentor biriktiradi.
  * Mentor — o'z guruhlariga kelgan ro'yxatdan o'tish so'rovlarini tasdiqlaydi
    va o'quvchilarni guruhlar orasida ko'chiradi.
  * O'quvchi — ro'yxatdan o'tishda guruh tanlaydi va mentor tasdig'ini kutadi.
"""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Dushanba"
    TUESDAY = 1, "Seshanba"
    WEDNESDAY = 2, "Chorshanba"
    THURSDAY = 3, "Payshanba"
    FRIDAY = 4, "Juma"
    SATURDAY = 5, "Shanba"
    SUNDAY = 6, "Yakshanba"


class Group(BaseModel):
    """Kurs ichidagi o'quv guruhi — manager yaratadi, mentor boshqaradi."""

    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=120)  # masalan "Frontend — kechki"
    code = models.SlugField(max_length=60, unique=True)  # masalan "frontend-01"

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mentored_groups",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="managed_groups",
    )

    capacity = models.PositiveSmallIntegerField(default=30)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)

    # Ro'yxatdan o'tish formasida shu guruh ko'rinadimi
    is_open_for_registration = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "groups_group"
        ordering = ["name"]
        indexes = [models.Index(fields=["course", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def active_members_count(self) -> int:
        return self.memberships.filter(status=MembershipStatus.ACTIVE).count()

    @property
    def has_free_seats(self) -> bool:
        return self.active_members_count < self.capacity


class GroupSchedule(BaseModel):
    """Dars vaqtlari — manager belgilaydi (hafta kuni + vaqt oralig'i)."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="schedules")
    weekday = models.SmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=60, blank=True)
    online_url = models.URLField(blank=True)

    class Meta:
        db_table = "groups_group_schedule"
        ordering = ["weekday", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "weekday", "start_time"], name="uniq_group_schedule_slot",
            ),
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="schedule_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    TRANSFERRED = "transferred", "Boshqa guruhga ko'chirilgan"
    REMOVED = "removed", "Chiqarilgan"


class GroupMembership(BaseModel):
    """O'quvchining guruhdagi a'zoligi. Ko'chirish tarixi saqlanadi."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships",
    )
    status = models.CharField(max_length=20, choices=MembershipStatus.choices, default=MembershipStatus.ACTIVE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )

    class Meta:
        db_table = "groups_membership"
        ordering = ["-joined_at"]
        constraints = [
            # Bir o'quvchi bitta guruhda faqat bitta FAOL a'zolikka ega bo'ladi;
            # ko'chirilgan/chiqarilgan yozuvlar tarix sifatida qoladi.
            models.UniqueConstraint(
                fields=["group", "student"],
                condition=models.Q(status="active"),
                name="uniq_active_membership_per_group",
            ),
        ]
        indexes = [models.Index(fields=["student", "status"])]

    def __str__(self):
        return f"{self.student} @ {self.group}"


class JoinRequestStatus(models.TextChoices):
    PENDING = "pending", "Tasdiqlash kutilmoqda"
    APPROVED = "approved", "Tasdiqlangan"
    REJECTED = "rejected", "Rad etilgan"


class JoinRequest(BaseModel):
    """
    O'quvchi ro'yxatdan o'tganda tanlagan guruhga qo'shilish so'rovi.
    Mentor tasdiqlagandan keyingina o'quvchi guruhga (va kursga) kiradi.
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="join_requests",
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="join_requests")
    status = models.CharField(max_length=20, choices=JoinRequestStatus.choices, default=JoinRequestStatus.PENDING)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_join_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField(max_length=255, blank=True)  # rad etish sababi

    class Meta:
        db_table = "groups_join_request"
        ordering = ["created_at"]
        constraints = [
            # Bir o'quvchida bir guruhga bir vaqtda faqat bitta kutilayotgan so'rov
            models.UniqueConstraint(
                fields=["student", "group"],
                condition=models.Q(status="pending"),
                name="uniq_pending_join_request",
            ),
        ]
        indexes = [models.Index(fields=["group", "status"])]

    def __str__(self):
        return f"{self.student} -> {self.group} [{self.status}]"
