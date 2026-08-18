from rest_framework import serializers

from apps.assignments.models import Grade, Submission, SubmissionStatus
from apps.core.fields import I18nCharField


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
    user_name = serializers.CharField(source="user.display_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    lesson_title = I18nCharField(source="homework.lesson.title")
    deadline_at = serializers.DateTimeField(source="homework.deadline_at", read_only=True)
    max_score = serializers.IntegerField(source="homework.max_score", read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id", "homework", "user", "user_name", "username", "mentor",
            "file", "text", "link", "status", "status_label", "submitted_at",
            "is_late", "deadline_at", "lesson_title", "max_score", "grade",
        )
        read_only_fields = ("status", "submitted_at", "is_late", "mentor")


class GradeSubmitSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=100)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
    needs_revision = serializers.BooleanField(default=False)


class StatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SubmissionStatus.choices)


class StudentOverviewSerializer(serializers.Serializer):
    """Mentor monitoringi jadvalidagi qator (groups.monitoring.StudentRow)."""

    id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    group_id = serializers.CharField(read_only=True)
    group_name = serializers.CharField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True, allow_null=True)
    days_since_login = serializers.IntegerField(read_only=True, allow_null=True)
    progress_percent = serializers.FloatField(read_only=True)
    completed_lessons = serializers.IntegerField(read_only=True)
    pending_submissions = serializers.IntegerField(read_only=True)
    overdue_submissions = serializers.IntegerField(read_only=True)
    at_risk = serializers.BooleanField(read_only=True)
    risk_reasons = serializers.ListField(child=serializers.CharField(), read_only=True)
