"""Mentor kontent boshqaruvi uchun serializerlar — /api/v1/mentor/ ostida."""

from rest_framework import serializers

from apps.core.fields import I18nCharField
from apps.courses.api.serializers import FileAssetSerializer, VideoAssetSerializer
from apps.courses.constants import ALLOWED_MATERIAL_EXTENSIONS, MAX_MATERIAL_SIZE_BYTES, MAX_MATERIAL_SIZE_MB
from apps.courses.models import Course, Lesson, LessonType, MaterialKind, Module


class MentorLessonSerializer(serializers.ModelSerializer):
    title = I18nCharField()
    text_content = I18nCharField()
    materials = FileAssetSerializer(many=True, read_only=True)
    video_asset = VideoAssetSerializer(read_only=True)
    quiz_id = serializers.SerializerMethodField()
    homework_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id", "type", "title", "text_content", "order", "is_required",
            "is_free_preview", "materials", "video_asset", "quiz_id", "homework_id",
        )

    def get_quiz_id(self, obj) -> str | None:
        return str(obj.quiz.id) if hasattr(obj, "quiz") else None

    def get_homework_id(self, obj) -> str | None:
        return str(obj.homework.id) if hasattr(obj, "homework") else None


class MentorModuleSerializer(serializers.ModelSerializer):
    title = I18nCharField()
    lessons = MentorLessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ("id", "title", "order", "lessons")


class MentorCourseSerializer(serializers.ModelSerializer):
    title = I18nCharField()
    modules = MentorModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ("id", "slug", "title", "modules")


class ModuleWriteSerializer(serializers.Serializer):
    title = serializers.JSONField()


class LessonWriteSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=LessonType.choices)
    title = serializers.JSONField()
    text_content = serializers.JSONField(required=False, default=dict)
    is_required = serializers.BooleanField(default=True)
    is_free_preview = serializers.BooleanField(default=False)


class MaterialUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    kind = serializers.ChoiceField(choices=MaterialKind.choices)
    is_downloadable = serializers.BooleanField(default=True)

    def validate_file(self, value):
        ext = value.name.rsplit(".", 1)[-1].lower() if "." in value.name else ""
        if ext not in ALLOWED_MATERIAL_EXTENSIONS:
            raise serializers.ValidationError(
                f"Ruxsat etilmagan fayl turi ('.{ext}'). Ruxsat etilgan turlar: "
                + ", ".join(sorted(ALLOWED_MATERIAL_EXTENSIONS)) + ".",
            )
        if value.size > MAX_MATERIAL_SIZE_BYTES:
            raise serializers.ValidationError(
                f"Fayl hajmi {MAX_MATERIAL_SIZE_MB} MB dan oshmasligi kerak "
                f"(yuborilgan: {value.size / 1024 / 1024:.1f} MB).",
            )
        return value
