"""TZ 4.11 (TE01-TE05): O'qituvchi kabineti."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import DomainError
from apps.courses import selectors, services
from apps.courses.api.serializers import (
    CourseCreateSerializer,
    LessonCreateSerializer,
    ModerationDecisionSerializer,
    ModuleCreateSerializer,
    ReorderSerializer,
    TeacherCourseListSerializer,
)
from apps.courses.models import Course, Module


class TeacherCourseViewSet(viewsets.ModelViewSet):
    """TE-01: kurslarim — yaratish, tahrirlash, moderatsiyaga yuborish, statistika."""

    permission_classes = [IsAuthenticated]
    serializer_class = TeacherCourseListSerializer

    def get_queryset(self):
        return selectors.get_teacher_courses(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = CourseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = services.create_course(author=request.user, **serializer.validated_data)
        return Response(TeacherCourseListSerializer(course).data, status=status.HTTP_201_CREATED)

    def get_object(self):
        return Course.objects.get(id=self.kwargs["pk"], author=self.request.user)

    @action(detail=True, methods=["post"], url_path="modules")
    def add_module(self, request, pk=None):
        course = self.get_object()
        serializer = ModuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = services.add_module(course=course, **serializer.validated_data)
        return Response({"id": str(module.id)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="modules/reorder")
    def reorder_modules(self, request, pk=None):
        course = self.get_object()
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reorder_modules(course=course, ordered_ids=serializer.validated_data["ordered_ids"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path=r"modules/(?P<module_id>[^/.]+)/lessons")
    def add_lesson(self, request, pk=None, module_id=None):
        course = self.get_object()
        module = Module.objects.get(id=module_id, course=course)
        serializer = LessonCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = services.add_lesson(module=module, **serializer.validated_data)
        return Response({"id": str(lesson.id)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        course = self.get_object()
        try:
            services.submit_for_moderation(actor=request.user, course=course)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response({"status": course.status})

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicate(self, request, pk=None):
        course = self.get_object()
        new_course = services.duplicate_course(actor=request.user, course=course)
        return Response(TeacherCourseListSerializer(new_course).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="students")
    def students(self, request, pk=None):
        """TE-02"""
        course = self.get_object()
        from apps.enrollment.selectors import get_course_students

        return Response(get_course_students(course))

    @action(detail=True, methods=["get"], url_path="analytics")
    def analytics(self, request, pk=None):
        """TE-03"""
        course = self.get_object()
        from apps.analytics.selectors import get_course_analytics

        return Response(get_course_analytics(course))

    @action(detail=True, methods=["get"], url_path="earnings")
    def earnings(self, request, pk=None):
        """TE-04"""
        course = self.get_object()
        from apps.payouts.selectors import get_course_earnings

        return Response(get_course_earnings(course))


class ModerationViewSet(viewsets.ViewSet):
    """AD-02: kurslar moderatsiyasi — admin uchun."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        from apps.courses.api.serializers import TeacherCourseListSerializer

        return Response(TeacherCourseListSerializer(selectors.get_moderation_queue(), many=True).data)

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        course = Course.objects.get(id=pk)
        serializer = ModerationDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.moderate_course(actor=request.user, course=course, **serializer.validated_data)
        return Response({"status": course.status})
