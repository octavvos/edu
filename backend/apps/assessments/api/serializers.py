import random

from rest_framework import serializers

from apps.assessments.models import Attempt, Choice, Question


class ChoiceForAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text")  # is_correct qaytarilmaydi — T-02


class QuestionForAttemptSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ("id", "type", "text", "points", "choices")

    def get_choices(self, obj):
        choices = list(obj.choices.all())
        if obj.quiz.randomize_choices:
            # Attempt ID'ga bog'liq deterministik aralashtirish — sahifa
            # yangilanganda tartib o'zgarib ketmaydi (T-02).
            seed = self.context.get("attempt_id", "")
            random.Random(f"{seed}:{obj.id}").shuffle(choices)
        return ChoiceForAttemptSerializer(choices, many=True).data


class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ("id", "status", "started_at", "expires_at", "score_percent", "passed")


class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_choice_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    text_answer = serializers.CharField(required=False, allow_blank=True, default="")
