"""Mentor kontent boshqaruvi: materiallar yuklash, modul/dars qo'shish."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import DomainError
from apps.courses import selectors, services
from apps.courses.api.mentor_serializers import (
    LessonWriteSerializer,
    MaterialUploadSerializer,
    MentorCourseSerializer,
    MentorLessonSerializer,
    ModuleWriteSerializer,
)
from apps.courses.models import Course, FileAsset, Lesson, Module
from apps.rbac.permissions import HasPermission


class MentorCourseListView(APIView):
    """GET /api/v1/mentor/courses/ — mentor biriktirilgan guruhlarning kurslari, to'liq struktura bilan."""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    @extend_schema(responses=MentorCourseSerializer(many=True))
    def get(self, request):
        courses = selectors.get_mentor_courses(request.user).prefetch_related(
            "modules__lessons__materials", "modules__lessons__video_asset", "modules__lessons__quiz",
        )
        return Response(
            MentorCourseSerializer(courses, many=True, context={"request": request}).data,
        )


class MentorModuleCreateView(APIView):
    """POST /api/v1/mentor/courses/{course_id}/modules/"""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    @extend_schema(request=ModuleWriteSerializer)
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        try:
            services.assert_mentor_owns_course(mentor=request.user, course=course)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = ModuleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = services.add_module(course=course, **serializer.validated_data)
        return Response({"id": str(module.id)}, status=status.HTTP_201_CREATED)


class MentorLessonCreateView(APIView):
    """POST /api/v1/mentor/modules/{module_id}/lessons/"""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    @extend_schema(request=LessonWriteSerializer, responses=MentorLessonSerializer)
    def post(self, request, module_id):
        module = get_object_or_404(Module.objects.select_related("course"), id=module_id)
        try:
            services.assert_mentor_owns_course(mentor=request.user, course=module.course)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = LessonWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = services.add_lesson(module=module, **serializer.validated_data)
        return Response(
            MentorLessonSerializer(lesson, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MentorMaterialUploadView(APIView):
    """
    POST /api/v1/mentor/lessons/{lesson_id}/material/ — fayl material yuklash
    (hujjat, slayd, qo'shimcha manba). MinIO/S3'ga haqiqiy saqlanadi.
    """

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(request=MaterialUploadSerializer, responses=MentorLessonSerializer)
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson.objects.select_related("module__course"), id=lesson_id)
        try:
            services.assert_can_manage_lesson(mentor=request.user, lesson=lesson)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        serializer = MaterialUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.add_file_material(
            lesson=lesson,
            file=serializer.validated_data["file"],
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            kind=serializer.validated_data["kind"],
            is_downloadable=serializer.validated_data["is_downloadable"],
        )
        lesson.refresh_from_db()
        return Response(
            MentorLessonSerializer(lesson, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MentorMaterialDeleteView(APIView):
    """DELETE /api/v1/mentor/materials/{material_id}/"""

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "content.manage"

    def delete(self, request, material_id):
        material = get_object_or_404(
            FileAsset.objects.select_related("lesson__module__course"), id=material_id,
        )
        try:
            services.remove_file_material(mentor=request.user, material=material)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(status=status.HTTP_204_NO_CONTENT)
