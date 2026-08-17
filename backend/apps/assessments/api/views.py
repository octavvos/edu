from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments import services
from apps.assessments.api.serializers import (
    AnswerSubmitSerializer,
    AttemptSerializer,
    QuestionForAttemptSerializer,
)
from apps.assessments.models import Attempt, Question, Quiz
from apps.core.exceptions import DomainError


class QuizStartView(APIView):
    """POST /api/v1/assessments/quizzes/{lesson_id}/start/"""

    def post(self, request, lesson_id):
        quiz = Quiz.objects.filter(lesson_id=lesson_id).first()
        if not quiz:
            return Response(status=status.HTTP_404_NOT_FOUND)

        from apps.enrollment.services import assert_lesson_access

        try:
            enrollment = assert_lesson_access(user=request.user, lesson=quiz.lesson)
            attempt = services.start_attempt(user=request.user, enrollment=enrollment, quiz=quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        questions = Question.objects.filter(id__in=attempt.question_ids).prefetch_related("choices")
        # question_ids tartibini saqlab qolamiz (T-01/T-02)
        ordered = sorted(questions, key=lambda q: attempt.question_ids.index(str(q.id)))
        data = {
            "attempt": AttemptSerializer(attempt).data,
            "questions": QuestionForAttemptSerializer(
                ordered, many=True, context={"attempt_id": str(attempt.id)},
            ).data,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class QuizAnswerView(APIView):
    """POST /api/v1/assessments/attempts/{attempt_id}/answer/"""

    def post(self, request, attempt_id):
        attempt = Attempt.objects.filter(id=attempt_id, user=request.user).first()
        if not attempt:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = Question.objects.filter(id=serializer.validated_data["question_id"]).first()
        if not question:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            services.submit_answer(
                attempt=attempt, question=question,
                selected_choice_ids=serializer.validated_data["selected_choice_ids"],
                text_answer=serializer.validated_data["text_answer"],
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response({"detail": "Javob qabul qilindi"})


class QuizSubmitView(APIView):
    """POST /api/v1/assessments/attempts/{attempt_id}/submit/"""

    def post(self, request, attempt_id):
        attempt = Attempt.objects.filter(id=attempt_id, user=request.user).first()
        if not attempt:
            return Response(status=status.HTTP_404_NOT_FOUND)
        attempt = services.finalize_attempt(attempt=attempt)
        result = AttemptSerializer(attempt).data
        if attempt.quiz.result_display == "never":
            result.pop("score_percent", None)
        return Response(result)


class AttemptListView(APIView):
    """GET /api/v1/assessments/attempts/?quiz_lesson_id=..."""

    def get(self, request):
        qs = Attempt.objects.filter(user=request.user)
        lesson_id = request.query_params.get("quiz_lesson_id")
        if lesson_id:
            qs = qs.filter(quiz__lesson_id=lesson_id)
        return Response(AttemptSerializer(qs.order_by("-started_at"), many=True).data)
