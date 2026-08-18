"""Mentor kontent boshqaruvi uchun serializerlar — /api/v1/mentor/ ostida."""

from rest_framework import serializers

from apps.core.fields import I18nCharField
from apps.courses.api.serializers import FileAssetSerializer, VideoAssetSerializer
from apps.courses.models import Course, Lesson, LessonType, Module


class MentorLessonSerializer(serializers.ModelSerializer):
    title = I18nCharField()
    text_content = I18nCharField()
    file_asset = FileAssetSerializer(read_only=True)
    video_asset = VideoAssetSerializer(read_only=True)
    quiz_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id", "type", "title", "text_content", "order", "is_required",
            "is_free_preview", "file_asset", "video_asset", "quiz_id",
        )

    def get_quiz_id(self, obj) -> str | None:
        return str(obj.quiz.id) if hasattr(obj, "quiz") else None


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
    is_downloadable = serializers.BooleanField(default=True)
