from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from apps.courses.models import Course, CourseVersion, FileAsset, Lesson, Module, VideoAsset


class LessonInline(TabularInline):
    model = Lesson
    extra = 0
    fields = ("type", "title", "order", "is_required", "is_free_preview")


class ModuleInline(StackedInline):
    model = Module
    extra = 0
    fields = ("title", "order")


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ("slug", "author", "status", "price", "enrollment_count", "rating_avg", "created_at")
    list_filter = ("status", "level", "language")
    search_fields = ("slug", "author__phone", "author__email")
    inlines = [ModuleInline]
    readonly_fields = ("enrollment_count", "rating_avg", "rating_count", "published_version", "published_at")
    actions = ["approve_courses", "reject_courses"]

    @admin.action(description="Tanlangan kurslarni tasdiqlash (nashr qilish)")
    def approve_courses(self, request, queryset):
        from apps.courses.services import moderate_course

        for course in queryset:
            moderate_course(actor=request.user, course=course, approve=True)

    @admin.action(description="Tanlangan kurslarni rad etish")
    def reject_courses(self, request, queryset):
        from apps.courses.services import moderate_course

        for course in queryset:
            moderate_course(actor=request.user, course=course, approve=False, reason="Admin tomonidan rad etildi")


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    list_display = ("course", "title", "order")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ("module", "type", "title", "order", "is_required", "is_free_preview")
    list_filter = ("type", "is_required", "is_free_preview")


@admin.register(VideoAsset)
class VideoAssetAdmin(ModelAdmin):
    list_display = ("original_filename", "provider", "status", "duration_seconds", "view_count")
    list_filter = ("status", "provider")


@admin.register(FileAsset)
class FileAssetAdmin(ModelAdmin):
    list_display = ("original_filename", "mime_type", "size_bytes", "is_downloadable")


@admin.register(CourseVersion)
class CourseVersionAdmin(ModelAdmin):
    list_display = ("course", "version_no", "published_at", "created_by")

    def has_change_permission(self, request, obj=None):
        return False
