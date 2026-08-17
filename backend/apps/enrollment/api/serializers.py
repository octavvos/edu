from rest_framework import serializers

from apps.enrollment.models import LessonNote


class ProgressUpdateSerializer(serializers.Serializer):
    seconds_watched = serializers.IntegerField(min_value=0, default=0)
    last_position = serializers.IntegerField(min_value=0, default=0)
    mark_completed = serializers.BooleanField(default=False)


class LessonNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonNote
        fields = ("id", "text", "video_timestamp_seconds", "created_at")
        read_only_fields = ("id", "created_at")
