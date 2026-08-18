"""
TZ 4.4 (C01-C07), 4.5 (V01-V10), 5.4, 5.5 — kurs strukturasi va konstruktori.
Iyerarxiya: Course -> Module -> Lesson. Video/Fayl assetlar shu app'da,
chunki ular Lesson'ga bevosita tegishli (bounded context: "kontent").
"""

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from apps.core.models import BaseModel, OrgScopedBaseModel, StatusChoices, i18n_field


class CourseLevel(models.TextChoices):
    BEGINNER = "beginner", "Boshlang'ich"
    INTERMEDIATE = "intermediate", "O'rta"
    ADVANCED = "advanced", "Yuqori"


class Course(OrgScopedBaseModel):
    """D-02: organization_id — B2B litsenziyalash uchun tayyor (MVP'da har doim null)."""

    slug = models.SlugField(max_length=180, unique=True)
    title = i18n_field()  # D-04
    description = i18n_field()
    requirements = i18n_field()  # K-06: talablar
    outcomes = i18n_field()  # K-06: natijalar

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="authored_courses",
    )
    category = models.ForeignKey(
        "catalog.Category", on_delete=models.SET_NULL, null=True, related_name="courses",
    )

    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)  # C-02
    rejection_reason = models.TextField(blank=True)  # AD-02

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="UZS")
    level = models.CharField(max_length=20, choices=CourseLevel.choices, default=CourseLevel.BEGINNER)
    language = models.CharField(max_length=10, default="uz")

    cover_image = models.FileField(upload_to="courses/covers/", null=True, blank=True)
    trailer_video = models.ForeignKey(
        "courses.VideoAsset", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )

    issues_certificate = models.BooleanField(default=True)
    duration_minutes = models.PositiveIntegerField(default=0)  # avtomatik hisoblanadi (darslar yig'indisi)

    published_version = models.ForeignKey(
        "courses.CourseVersion", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )  # C-03
    published_at = models.DateTimeField(null=True, blank=True)

    # Denormalizatsiya — tez o'qish uchun (5.10, K-03 saralash)
    enrollment_count = models.PositiveIntegerField(default=0)
    rating_avg = models.FloatField(default=0)
    rating_count = models.PositiveIntegerField(default=0)

    # K-04: qidiruv (5.9)
    title_plain = models.CharField(max_length=255, blank=True)
    description_plain = models.TextField(blank=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        db_table = "courses_course"
        indexes = [
            GinIndex(fields=["search_vector"]),
            models.Index(fields=["status", "category"]),
        ]

    def __str__(self):
        return self.slug


class CourseVersion(BaseModel):
    """C-03: nashr etilgan kursning versiyalanishi — tahrirlash yangi qoralama versiyada."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="versions")
    version_no = models.PositiveIntegerField()
    snapshot = models.JSONField()  # to'liq modul/dars strukturasi shu versiya nashr etilgan paytda
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "courses_course_version"
        constraints = [
            models.UniqueConstraint(fields=["course", "version_no"], name="uniq_course_version_no"),
        ]
        ordering = ["-version_no"]


class Module(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = i18n_field()
    order = models.PositiveIntegerField(default=0)  # C-01: drag-and-drop

    class Meta:
        db_table = "courses_module"
        ordering = ["order"]
        indexes = [models.Index(fields=["course", "order"])]


class LessonType(models.TextChoices):
    """4.4-band: 5 ta dars turi."""

    VIDEO = "video", "Video dars"
    TEXT = "text", "Matnli dars"
    FILE = "file", "Fayl / material"
    QUIZ = "quiz", "Test / kviz"
    HOMEWORK = "homework", "Uy vazifasi"


class Lesson(BaseModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    type = models.CharField(max_length=20, choices=LessonType.choices)
    title = i18n_field()
    text_content = i18n_field()  # matnli dars uchun WYSIWYG HTML

    order = models.PositiveIntegerField(default=0)  # C-01
    is_required = models.BooleanField(default=True)  # C-06
    is_free_preview = models.BooleanField(default=False)  # K-07

    video_asset = models.OneToOneField(
        "courses.VideoAsset", on_delete=models.SET_NULL, null=True, blank=True, related_name="lesson",
    )
    # Bitta darsga bir nechta fayl material yuklash mumkin (slaydlar + amaliy
    # fayl + qo'shimcha o'qish kabi) — shuning uchun FileAsset tomonidan FK
    # (apps.courses.FileAsset.lesson), bu yerda OneToOne emas.

    unlock_rule = models.JSONField(default=dict, blank=True)
    """
    C-05 (drip content):
        {"type": "date", "unlock_at": "2026-01-01T00:00:00Z"}
        {"type": "after_lesson", "lesson_id": "<uuid>"}
        {"type": "min_quiz_score", "quiz_lesson_id": "<uuid>", "min_percent": 70}
        {} — cheklovsiz, darhol ochiq
    """

    class Meta:
        db_table = "courses_lesson"
        ordering = ["order"]
        indexes = [models.Index(fields=["module", "order"])]


class VideoAssetStatus(models.TextChoices):
    UPLOADING = "uploading", "Yuklanmoqda"
    PROCESSING = "processing", "Transkodlanmoqda"
    READY = "ready", "Tayyor"
    FAILED = "failed", "Xatolik"


class VideoAsset(BaseModel):
    """D-11: provayder abstraksiyasi — Bunny Stream (I-03), kelajakda almashtirilishi mumkin."""

    provider = models.CharField(max_length=30, default="bunny")
    external_id = models.CharField(max_length=100, blank=True)  # Bunny video GUID
    manifest_url = models.URLField(blank=True)  # HLS .m3u8 — V-02
    status = models.CharField(max_length=20, choices=VideoAssetStatus.choices, default=VideoAssetStatus.UPLOADING)

    original_filename = models.CharField(max_length=255, blank=True)
    size_bytes = models.BigIntegerField(default=0)  # V-08: max >= 5GB
    duration_seconds = models.PositiveIntegerField(default=0)
    subtitles = models.JSONField(default=list, blank=True)  # V-04: [{"lang": "uz", "url": "..."}]

    view_count = models.PositiveIntegerField(default=0)  # V-10
    total_watched_seconds = models.BigIntegerField(default=0)  # V-10: o'rtacha koʻrilgan foiz uchun

    class Meta:
        db_table = "courses_video_asset"

    @property
    def average_watched_percent(self) -> float:
        if not self.duration_seconds or not self.view_count:
            return 0.0
        return min(100.0, (self.total_watched_seconds / self.view_count) / self.duration_seconds * 100)


class FileAsset(BaseModel):
    """
    Darsga biriktirilgan qo'shimcha material (slayd, hujjat va h.k.).
    Bitta darsga bir nechtasi biriktirilishi mumkin (`lesson.materials`).
    """

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name="materials",
    )
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="courses/files/")
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    is_downloadable = models.BooleanField(default=True)

    class Meta:
        db_table = "courses_file_asset"
        ordering = ["created_at"]
