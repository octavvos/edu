"""Mentor test builder'i — /api/v1/mentor/ ostida."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments import services
from apps.assessments.api.mentor_serializers import (
    QuestionMentorSerializer,
    QuestionUpdateSerializer,
    QuestionWriteSerializer,
    QuizAssignSerializer,
    QuizAssignmentSerializer,
    QuizDetailSerializer,
    QuizSettingsSerializer,
)
from apps.assessments.models import Question, Quiz
from apps.core.exceptions import DomainError
from apps.courses.models import Lesson
from apps.courses.services import assert_can_manage_lesson
from apps.rbac.permissions import HasPermission


def _assert_owns_quiz(mentor, quiz: Quiz) -> None:
    assert_can_manage_lesson(mentor=mentor, lesson=quiz.lesson)


class MentorQuizCreateView(APIView):
    """POST /api/v1/mentor/lessons/{lesson_id}/quiz/ — darsga test ochish."""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    @extend_schema(request=QuizSettingsSerializer, responses=QuizDetailSerializer)
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson.objects.select_related("module__course"), id=lesson_id)
        try:
            assert_can_manage_lesson(mentor=request.user, lesson=lesson)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = QuizSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            quiz = services.create_quiz(lesson=lesson, **serializer.validated_data)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(QuizDetailSerializer(quiz).data, status=status.HTTP_201_CREATED)


class MentorQuizDetailView(APIView):
    """GET/PUT /api/v1/mentor/quizzes/{quiz_id}/"""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    def _get_quiz(self, quiz_id):
        return get_object_or_404(
            Quiz.objects.select_related("lesson__module__course"), id=quiz_id,
        )

    @extend_schema(responses=QuizDetailSerializer)
    def get(self, request, quiz_id):
        quiz = self._get_quiz(quiz_id)
        try:
            _assert_owns_quiz(request.user, quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(QuizDetailSerializer(quiz).data)

    @extend_schema(request=QuizSettingsSerializer, responses=QuizDetailSerializer)
    def put(self, request, quiz_id):
        quiz = self._get_quiz(quiz_id)
        try:
            _assert_owns_quiz(request.user, quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = QuizSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        quiz = services.update_quiz(quiz=quiz, **serializer.validated_data)
        return Response(QuizDetailSerializer(quiz).data)


class MentorQuestionListCreateView(APIView):
    """GET/POST /api/v1/mentor/quizzes/{quiz_id}/questions/"""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    @extend_schema(responses=QuestionMentorSerializer(many=True))
    def get(self, request, quiz_id):
        quiz = get_object_or_404(
            Quiz.objects.select_related("lesson__module__course"), id=quiz_id,
        )
        try:
            _assert_owns_quiz(request.user, quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        questions = quiz.questions.prefetch_related("choices").order_by("order")
        return Response(
            QuestionMentorSerializer(questions, many=True, context={"request": request}).data,
        )

    @extend_schema(request=QuestionWriteSerializer, responses=QuestionMentorSerializer)
    def post(self, request, quiz_id):
        quiz = get_object_or_404(
            Quiz.objects.select_related("lesson__module__course"), id=quiz_id,
        )
        try:
            _assert_owns_quiz(request.user, quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = QuestionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            question = services.add_question(quiz=quiz, **serializer.validated_data)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(
            QuestionMentorSerializer(question, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MentorQuestionDetailView(APIView):
    """PUT/DELETE /api/v1/mentor/questions/{question_id}/"""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    def _get_question(self, question_id):
        return get_object_or_404(
            Question.objects.select_related("quiz__lesson__module__course"), id=question_id,
        )

    @extend_schema(request=QuestionUpdateSerializer, responses=QuestionMentorSerializer)
    def put(self, request, question_id):
        question = self._get_question(question_id)
        try:
            _assert_owns_quiz(request.user, question.quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = QuestionUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            question = services.update_question(question=question, **serializer.validated_data)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(QuestionMentorSerializer(question, context={"request": request}).data)

    def delete(self, request, question_id):
        question = self._get_question(question_id)
        try:
            _assert_owns_quiz(request.user, question.quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        services.delete_question(question=question)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MentorQuizAssignmentView(APIView):
    """
    GET    /api/v1/mentor/lessons/{lesson_id}/quiz-assignment/ — shu testga
           qaysi guruhlar jo'natilgani
    POST   /api/v1/mentor/lessons/{lesson_id}/quiz-assignment/ — tanlangan
           guruhga jo'natish
    DELETE /api/v1/mentor/lessons/{lesson_id}/quiz-assignment/?group_id=... —
           guruhdan bekor qilish
    """

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    def _get_quiz(self, lesson_id):
        lesson = get_object_or_404(Lesson.objects.select_related("module__course"), id=lesson_id)
        quiz = get_object_or_404(Quiz.objects.select_related("lesson__module__course"), lesson=lesson)
        return quiz

    def get(self, request, lesson_id):
        quiz = self._get_quiz(lesson_id)
        try:
            _assert_owns_quiz(request.user, quiz)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        assignments = quiz.assignments.select_related("group").filter(group__mentor=request.user).order_by("group__name")
        return Response(QuizAssignmentSerializer(assignments, many=True).data)

    @extend_schema(request=QuizAssignSerializer, responses=QuizAssignmentSerializer)
    def post(self, request, lesson_id):
        from apps.groups.models import Group

        quiz = self._get_quiz(lesson_id)
        serializer = QuizAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = get_object_or_404(Group, id=serializer.validated_data["group_id"])

        try:
            assignment = services.assign_quiz_to_group(mentor=request.user, quiz=quiz, group=group)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(QuizAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    def delete(self, request, lesson_id):
        from apps.groups.models import Group

        quiz = self._get_quiz(lesson_id)
        group_id = request.query_params.get("group_id")
        if not group_id:
            return Response({"detail": "group_id talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
        group = get_object_or_404(Group, id=group_id)

        try:
            services.unassign_quiz_from_group(mentor=request.user, quiz=quiz, group=group)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(status=status.HTTP_204_NO_CONTENT)
