from rest_framework import serializers

from apps.assignments.models import Grade, Submission


class SubmissionCreateSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    text = serializers.CharField(required=False, allow_blank=True, default="")
    link = serializers.URLField(required=False, allow_blank=True, default="")


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ("score", "feedback", "graded_at")


class SubmissionSerializer(serializers.ModelSerializer):
    grade = GradeSerializer(read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id", "homework", "user", "user_name", "mentor", "file", "text", "link",
            "status", "submitted_at", "is_late", "grade",
        )
        read_only_fields = ("status", "submitted_at", "is_late", "mentor")


class GradeSubmitSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=100)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
    needs_revision = serializers.BooleanField(default=False)
