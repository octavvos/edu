from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assignments import services
from apps.assignments.api.serializers import (
    GradeSubmitSerializer,
    SubmissionCreateSerializer,
    SubmissionSerializer,
)
from apps.assignments.models import Homework, Submission
from apps.core.exceptions import DomainError


class HomeworkSubmitView(APIView):
    """POST /api/v1/assignments/{lesson_id}/submissions/ — H-01"""

    def post(self, request, lesson_id):
        homework = Homework.objects.select_related("lesson__module__course").filter(lesson_id=lesson_id).first()
        if not homework:
            return Response(status=status.HTTP_404_NOT_FOUND)

        from apps.enrollment.services import assert_lesson_access

        try:
            enrollment = assert_lesson_access(user=request.user, lesson=homework.lesson)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submission = services.submit_homework(
                user=request.user, enrollment=enrollment, homework=homework, **serializer.validated_data,
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class MentorQueueView(APIView):
    """Mentor kabineti — TZ 3.1 rol #4."""

    def get(self, request):
        from apps.assignments.selectors import get_mentor_queue

        return Response(SubmissionSerializer(get_mentor_queue(request.user), many=True).data)


class SubmissionGradeView(APIView):
    """POST /api/v1/assignments/submissions/{id}/grade/ — H-04"""

    def post(self, request, submission_id):
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if submission.mentor_id != request.user.id and not request.user.has_perm_scoped("assignment.grade"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = GradeSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submission = services.grade_submission(mentor=request.user, submission=submission, **serializer.validated_data)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(SubmissionSerializer(submission).data)


class GradebookView(APIView):
    """H-06: baholar jurnali."""

    def get(self, request, course_id):
        from apps.assignments.selectors import get_gradebook
        from apps.courses.models import Course

        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(SubmissionSerializer(get_gradebook(course), many=True).data)
