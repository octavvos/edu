"""Mentor test builder'i uchun serializerlar."""

from rest_framework import serializers

from apps.assessments.models import Choice, Question, QuestionType, Quiz, QuizAssignment
from apps.core.fields import I18nCharField


class QuizAssignmentSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = QuizAssignment
        fields = ("id", "quiz", "group", "group_name")


class QuizAssignSerializer(serializers.Serializer):
    group_id = serializers.UUIDField()


class QuizSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = (
            "time_limit_seconds", "questions_per_attempt", "randomize_questions",
            "randomize_choices", "max_attempts", "pass_percent", "retake_cooldown_hours",
            "result_display",
        )
        extra_kwargs = {field: {"required": False} for field in fields}


class QuizDetailSerializer(serializers.ModelSerializer):
    """Mentor ko'rinishi — to'g'ri javoblar bilan (student ko'rmaydigan)."""

    question_count = serializers.IntegerField(source="questions.count", read_only=True)

    class Meta:
        model = Quiz
        fields = (
            "id", "lesson", "time_limit_seconds", "questions_per_attempt",
            "randomize_questions", "randomize_choices", "max_attempts",
            "pass_percent", "retake_cooldown_hours", "result_display", "question_count",
        )


class ChoiceWriteSerializer(serializers.Serializer):
    text = serializers.JSONField()
    is_correct = serializers.BooleanField(default=False)


class ChoiceMentorSerializer(serializers.ModelSerializer):
    text = I18nCharField()

    class Meta:
        model = Choice
        fields = ("id", "text", "is_correct", "order")


class QuestionMentorSerializer(serializers.ModelSerializer):
    text = I18nCharField()
    explanation = I18nCharField()
    choices = ChoiceMentorSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = (
            "id", "type", "text", "explanation", "points", "order",
            "correct_text_pattern", "is_regex", "choices",
        )


class QuestionWriteSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=QuestionType.choices)
    text = serializers.JSONField()
    explanation = serializers.JSONField(required=False, default=dict)
    points = serializers.IntegerField(min_value=1, default=1)
    correct_text_pattern = serializers.CharField(required=False, allow_blank=True, default="")
    is_regex = serializers.BooleanField(default=False)
    choices = ChoiceWriteSerializer(many=True, required=False, default=list)


class QuestionUpdateSerializer(QuestionWriteSerializer):
    type = serializers.ChoiceField(choices=QuestionType.choices, required=False)
    text = serializers.JSONField(required=False)
    choices = ChoiceWriteSerializer(many=True, required=False, default=None, allow_null=True)


# ---------------------------------------------------------------------------
# Test natijalari tahlili (apps.assessments.selectors dataclass'lari bilan mos)
# ---------------------------------------------------------------------------


class GroupQuizSummarySerializer(serializers.Serializer):
    group_id = serializers.CharField()
    group_name = serializers.CharField()
    course_title = serializers.CharField()
    tests_sent = serializers.IntegerField()
    student_count = serializers.IntegerField()
    avg_score = serializers.FloatField(allow_null=True)
    completion_percent = serializers.FloatField()


class QuizLeaderboardRowSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    student_id = serializers.CharField()
    display_name = serializers.CharField()
    username = serializers.CharField()
    tests_assigned = serializers.IntegerField()
    tests_solved = serializers.IntegerField()
    avg_score = serializers.FloatField(allow_null=True)
    total_time_seconds = serializers.IntegerField()
    last_activity = serializers.CharField(allow_null=True)


class StudentQuizResultRowSerializer(serializers.Serializer):
    lesson_id = serializers.CharField()
    quiz_title = serializers.CharField()
    module_title = serializers.CharField()
    attempt_id = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    score_percent = serializers.FloatField(allow_null=True)
    passed = serializers.BooleanField(allow_null=True)
    time_taken_seconds = serializers.IntegerField(allow_null=True)
    submitted_at = serializers.CharField(allow_null=True)
    attempt_count = serializers.IntegerField()


class AnswerBreakdownRowSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    question_text = serializers.CharField()
    question_type = serializers.CharField()
    points = serializers.IntegerField()
    selected_choice_ids = serializers.ListField(child=serializers.CharField())
    selected_texts = serializers.ListField(child=serializers.CharField())
    correct_choice_ids = serializers.ListField(child=serializers.CharField())
    correct_texts = serializers.ListField(child=serializers.CharField())
    text_answer = serializers.CharField(allow_blank=True)
    is_correct = serializers.BooleanField(allow_null=True)
    points_awarded = serializers.FloatField()


class AttemptDetailSerializer(serializers.Serializer):
    attempt_id = serializers.CharField()
    quiz_title = serializers.CharField()
    student_display_name = serializers.CharField()
    score_percent = serializers.FloatField(allow_null=True)
    passed = serializers.BooleanField(allow_null=True)
    started_at = serializers.CharField()
    submitted_at = serializers.CharField(allow_null=True)
    time_taken_seconds = serializers.IntegerField(allow_null=True)
    answers = AnswerBreakdownRowSerializer(many=True)
