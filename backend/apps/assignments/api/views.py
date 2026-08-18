from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assignments import services
from apps.assignments.api.serializers import (
    GradeSubmitSerializer,
    HomeworkSendSerializer,
    HomeworkSerializer,
    MyAssignmentSerializer,
    StatusChangeSerializer,
    StudentOverviewSerializer,
    SubmissionCreateSerializer,
    SubmissionSerializer,
)
from apps.assignments.models import Homework, Submission
from apps.core.exceptions import DomainError
from apps.rbac.permissions import HasPermission


class HomeworkSubmitView(APIView):
    """POST /api/v1/assignments/{lesson_id}/submissions/ — H-01"""

    def post(self, request, lesson_id):
        from apps.groups.selectors import get_active_membership

        membership = get_active_membership(request.user)
        if not membership:
            return Response(
                {"detail": "Siz hech qaysi guruhga a'zo emassiz"}, status=status.HTTP_403_FORBIDDEN,
            )

        # Vazifa guruhga jo'natiladi — o'quvchi faqat o'z guruhinikini topshiradi.
        homework = (
            Homework.objects.select_related("lesson__module__course")
            .filter(lesson_id=lesson_id, group=membership.group)
            .first()
        )
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


class MentorHomeworkView(APIView):
    """
    GET  /api/v1/mentor/lessons/{lesson_id}/homework/ — shu darsga qaysi guruhlarga
         vazifa jo'natilgani (har biri o'z muddati/ballari bilan)
    POST /api/v1/mentor/lessons/{lesson_id}/homework/ — tanlangan guruhga jo'natish
    """

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    def get(self, request, lesson_id):
        from apps.courses.models import Lesson
        from apps.courses.services import assert_can_manage_lesson

        lesson = get_object_or_404(Lesson.objects.select_related("module__course"), id=lesson_id)
        try:
            assert_can_manage_lesson(mentor=request.user, lesson=lesson)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        homeworks = (
            Homework.objects.select_related("lesson", "group", "material", "presentation")
            .filter(lesson=lesson, group__mentor=request.user)
            .order_by("group__name")
        )
        return Response(HomeworkSerializer(homeworks, many=True, context={"request": request}).data)

    @extend_schema(request=HomeworkSendSerializer, responses=HomeworkSerializer)
    def post(self, request, lesson_id):
        from apps.courses.models import FileAsset, Lesson
        from apps.groups.models import Group

        lesson = get_object_or_404(Lesson.objects.select_related("module__course"), id=lesson_id)
        serializer = HomeworkSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group = get_object_or_404(Group, id=serializer.validated_data["group_id"])

        material = None
        material_id = serializer.validated_data.get("material_id")
        if material_id:
            material = get_object_or_404(FileAsset, id=material_id)

        presentation = None
        presentation_id = serializer.validated_data.get("presentation_id")
        if presentation_id:
            presentation = get_object_or_404(FileAsset, id=presentation_id)

        try:
            homework = services.send_homework(
                mentor=request.user, lesson=lesson, group=group,
                instructions=serializer.validated_data["instructions"],
                deadline_at=serializer.validated_data.get("deadline_at"),
                max_score=serializer.validated_data["max_score"],
                material=material,
                presentation=presentation,
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(
            HomeworkSerializer(homework, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MyAssignmentsView(APIView):
    """GET /api/v1/assignments/mine/ — o'quvchiga yuborilgan vazifalar + o'z topshirig'i/bahosi."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MyAssignmentSerializer(many=True))
    def get(self, request):
        from apps.assignments.selectors import get_my_assignments

        rows = get_my_assignments(request.user)
        return Response(MyAssignmentSerializer(rows, many=True, context={"request": request}).data)


class MentorQueueView(APIView):
    """
    GET /api/v1/mentor/submissions/ — tekshirilishi kerak bo'lgan topshiriqlar.
    `?status=` va `?group=` bilan filtrlanadi; `counts` holatlar bo'yicha sanoq.
    """

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "assignment.grade"

    @extend_schema(responses=SubmissionSerializer(many=True))
    def get(self, request):
        from apps.assignments.selectors import get_mentor_queue, get_mentor_queue_counts

        queue = get_mentor_queue(
            request.user,
            status=request.query_params.get("status", ""),
            group_id=request.query_params.get("group") or None,
        )
        return Response({
            "counts": get_mentor_queue_counts(request.user),
            "results": SubmissionSerializer(queue, many=True, context={"request": request}).data,
        })


class SubmissionStatusView(APIView):
    """POST /api/v1/mentor/submissions/{id}/status/ — H-03 holat o'tishlari."""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "assignment.grade"

    @extend_schema(request=StatusChangeSerializer, responses=SubmissionSerializer)
    def post(self, request, submission_id):
        submission = _get_submission(submission_id)
        if not submission:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submission = services.change_submission_status(
                mentor=request.user, submission=submission,
                new_status=serializer.validated_data["status"],
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(SubmissionSerializer(submission, context={"request": request}).data)


class MentorStudentsView(APIView):
    """
    GET /api/v1/mentor/students/ — o'ziga biriktirilgan o'quvchilar,
    progressi, oxirgi faolligi va "xavf ostida" belgisi bilan.
    """

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "group.view_own"

    @extend_schema(responses=StudentOverviewSerializer(many=True))
    def get(self, request):
        from apps.groups.monitoring import get_students_overview

        rows = get_students_overview(
            request.user, group_id=request.query_params.get("group") or None,
        )
        data = StudentOverviewSerializer(rows, many=True).data
        return Response({
            "at_risk_count": sum(1 for r in rows if r.at_risk),
            "total": len(rows),
            "results": data,
        })


class SubmissionGradeView(APIView):
    """POST /api/v1/mentor/submissions/{id}/grade/ — H-04"""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "assignment.grade"

    @extend_schema(request=GradeSubmitSerializer, responses=SubmissionSerializer)
    def post(self, request, submission_id):
        submission = _get_submission(submission_id)
        if not submission:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = GradeSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submission = services.grade_submission(
                mentor=request.user, submission=submission, **serializer.validated_data,
            )
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(SubmissionSerializer(submission, context={"request": request}).data)


def _get_submission(submission_id):
    return (
        Submission.objects
        .select_related("user", "grade", "homework", "homework__lesson")
        .filter(id=submission_id)
        .first()
    )


class GradebookView(APIView):
    """H-06: baholar jurnali."""

    def get(self, request, course_id):
        from apps.assignments.selectors import get_gradebook
        from apps.courses.models import Course

        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(SubmissionSerializer(get_gradebook(course), many=True).data)
