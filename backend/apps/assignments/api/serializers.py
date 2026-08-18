from rest_framework import serializers

from apps.assignments.constants import (
    ALLOWED_SUBMISSION_EXTENSIONS,
    MAX_SUBMISSION_SIZE_BYTES,
    MAX_SUBMISSION_SIZE_MB,
)
from apps.assignments.models import Grade, Homework, Submission, SubmissionStatus
from apps.core.fields import I18nCharField
from apps.courses.api.serializers import FileAssetSerializer


class SubmissionCreateSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    text = serializers.CharField(required=False, allow_blank=True, default="")
    link = serializers.URLField(required=False, allow_blank=True, default="")  # GitHub link — ixtiyoriy

    def validate_file(self, value):
        ext = value.name.rsplit(".", 1)[-1].lower() if "." in value.name else ""
        if ext not in ALLOWED_SUBMISSION_EXTENSIONS:
            raise serializers.ValidationError(
                f"Ruxsat etilmagan fayl turi ('.{ext}'). Faqat: "
                + ", ".join(sorted(ALLOWED_SUBMISSION_EXTENSIONS)) + " qabul qilinadi.",
            )
        if value.size > MAX_SUBMISSION_SIZE_BYTES:
            raise serializers.ValidationError(
                f"Fayl hajmi {MAX_SUBMISSION_SIZE_MB} MB dan oshmasligi kerak "
                f"(yuborilgan: {value.size / 1024 / 1024:.1f} MB).",
            )
        return value


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


class HomeworkSendSerializer(serializers.Serializer):
    """Mentor darsga vazifa yuboradi — nom/izoh mavjud materiallardan biriga ilova qilinishi mumkin."""

    instructions = serializers.JSONField()
    deadline_at = serializers.DateTimeField(required=False, allow_null=True, default=None)
    max_score = serializers.IntegerField(min_value=1, max_value=1000, default=100)
    material_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class HomeworkSerializer(serializers.ModelSerializer):
    instructions = I18nCharField()
    lesson_title = I18nCharField(source="lesson.title")
    material = FileAssetSerializer(read_only=True)

    class Meta:
        model = Homework
        fields = ("id", "lesson", "lesson_title", "instructions", "deadline_at", "max_score", "material")


class MySubmissionSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    grade = GradeSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = ("id", "file", "text", "link", "status", "status_label", "submitted_at", "is_late", "grade")


class MyAssignmentSerializer(serializers.ModelSerializer):
    """O'quvchiga yuborilgan vazifa + o'zining topshirig'i/bahosi (bo'lsa)."""

    instructions = I18nCharField()
    lesson_title = I18nCharField(source="lesson.title")
    material = FileAssetSerializer(read_only=True)
    submission = serializers.SerializerMethodField()

    class Meta:
        model = Homework
        fields = (
            "id", "lesson", "lesson_title", "instructions", "deadline_at",
            "max_score", "material", "submission",
        )

    def get_submission(self, obj):
        submission = getattr(obj, "_my_submission", None)
        return MySubmissionSerializer(submission, context=self.context).data if submission else None


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
