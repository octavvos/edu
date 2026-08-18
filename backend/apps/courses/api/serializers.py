from rest_framework import serializers

from apps.core.fields import I18nCharField
from apps.courses.models import Course, FileAsset, Lesson, Module, VideoAsset


class VideoAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoAsset
        fields = ("id", "status", "duration_seconds", "subtitles")  # manifest_url playback-token orqali beriladi


class FileAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAsset
        fields = ("id", "original_filename", "mime_type", "size_bytes", "is_downloadable")


class LessonPublicSerializer(serializers.ModelSerializer):
    """Syllabus'da ko'rsatiladi — kontent emas, faqat struktura (access nazorati enrollment'da)."""

    title = I18nCharField()

    class Meta:
        model = Lesson
        fields = ("id", "type", "title", "order", "is_required", "is_free_preview")


class LessonDetailSerializer(serializers.ModelSerializer):
    video_asset = VideoAssetSerializer(read_only=True)
    file_asset = FileAssetSerializer(read_only=True)
    title = I18nCharField()
    text_content = I18nCharField()

    class Meta:
        model = Lesson
        fields = (
            "id", "type", "title", "text_content", "order", "is_required",
            "is_free_preview", "unlock_rule", "video_asset", "file_asset",
        )


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ("type", "title", "text_content", "is_required", "is_free_preview", "unlock_rule")


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonPublicSerializer(many=True, read_only=True)
    title = I18nCharField()

    class Meta:
        model = Module
        fields = ("id", "title", "order", "lessons")


class ModuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ("title",)


class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source="author.display_name", read_only=True)
    title = I18nCharField()
    description = I18nCharField()
    requirements = I18nCharField()
    outcomes = I18nCharField()

    class Meta:
        model = Course
        fields = (
            "id", "slug", "title", "description", "requirements", "outcomes",
            "author", "author_name", "category", "status", "price", "currency",
            "level", "language", "cover_image", "issues_certificate",
            "duration_minutes", "rating_avg", "rating_count", "enrollment_count",
            "modules", "published_at",
        )


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "title", "description", "requirements", "outcomes", "category",
            "price", "currency", "level", "language", "issues_certificate", "cover_image",
        )


class TeacherCourseListSerializer(serializers.ModelSerializer):
    title = I18nCharField()

    class Meta:
        model = Course
        fields = (
            "id", "slug", "title", "status", "price", "enrollment_count",
            "rating_avg", "created_at", "published_at",
        )


class ReorderSerializer(serializers.Serializer):
    ordered_ids = serializers.ListField(child=serializers.UUIDField())


class ModerationDecisionSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
