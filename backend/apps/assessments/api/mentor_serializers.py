"""Mentor test builder'i uchun serializerlar."""

from rest_framework import serializers

from apps.assessments.models import Choice, Question, QuestionType, Quiz
from apps.core.fields import I18nCharField


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
