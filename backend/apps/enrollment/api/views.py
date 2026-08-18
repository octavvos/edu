from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import DomainError
from apps.courses.api.serializers import LessonDetailSerializer
from apps.courses.models import Lesson
from apps.enrollment import services
from apps.enrollment.api.serializers import LessonNoteSerializer, ProgressUpdateSerializer
from apps.enrollment.models import Enrollment, LessonNote


def _get_enrollment_and_lesson(request, enrollment_id, lesson_id):
    enrollment = Enrollment.objects.filter(id=enrollment_id, user=request.user).first()
    lesson = (
        Lesson.objects.select_related("video_asset")
        .prefetch_related("materials")
        .filter(id=lesson_id)
        .first()
    )
    return enrollment, lesson


class LessonLearnView(APIView):
    """GET /api/v1/learn/{enrollment}/lessons/{id}/"""

    def get(self, request, enrollment_id, lesson_id):
        enrollment, lesson = _get_enrollment_and_lesson(request, enrollment_id, lesson_id)
        if not lesson:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            services.assert_lesson_access(user=request.user, lesson=lesson)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(LessonDetailSerializer(lesson).data)


class LessonProgressView(APIView):
    """POST /api/v1/learn/{enrollment}/lessons/{id}/progress/"""

    def post(self, request, enrollment_id, lesson_id):
        enrollment, lesson = _get_enrollment_and_lesson(request, enrollment_id, lesson_id)
        if not enrollment or not lesson:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        progress = services.update_progress(enrollment=enrollment, lesson=lesson, **serializer.validated_data)
        return Response({"status": progress.status, "course_progress_percent": enrollment.progress_percent})


class PlaybackTokenView(APIView):
    """GET /api/v1/learn/{enrollment}/lessons/{id}/playback-token/ — V-06."""

    def get(self, request, enrollment_id, lesson_id):
        enrollment, lesson = _get_enrollment_and_lesson(request, enrollment_id, lesson_id)
        if not lesson:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            services.assert_lesson_access(user=request.user, lesson=lesson)
            token = services.get_playback_token(enrollment=enrollment, lesson=lesson)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(token)


class LessonNotesView(APIView):
    """GET/POST /api/v1/learn/{enrollment}/lessons/{id}/notes/"""

    def get(self, request, enrollment_id, lesson_id):
        enrollment, _ = _get_enrollment_and_lesson(request, enrollment_id, lesson_id)
        if not enrollment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        notes = LessonNote.objects.filter(enrollment=enrollment, lesson_id=lesson_id)
        return Response(LessonNoteSerializer(notes, many=True).data)

    def post(self, request, enrollment_id, lesson_id):
        enrollment, lesson = _get_enrollment_and_lesson(request, enrollment_id, lesson_id)
        if not enrollment or not lesson:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = LessonNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = LessonNote.objects.create(enrollment=enrollment, lesson=lesson, **serializer.validated_data)
        return Response(LessonNoteSerializer(note).data, status=status.HTTP_201_CREATED)
