from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import DomainError
from apps.courses import selectors
from apps.courses.api.serializers import CourseDetailSerializer, LessonDetailSerializer
from apps.rbac.permissions import IsApprovedStudent


class CourseDetailView(APIView):
    """
    GET /api/v1/courses/{slug}/ — kurs sahifasi.

    Mahsulot qoidasi: ro'yxatdan o'tmagan foydalanuvchi kursni ko'ra olmaydi,
    mentor tasdiqlamagan o'quvchi ham (IsApprovedStudent) ko'ra olmaydi.
    """

    permission_classes = [IsAuthenticated, IsApprovedStudent]

    def get(self, request, slug):
        course = selectors.get_published_course(slug=slug)
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(CourseDetailSerializer(course, context={"request": request}).data)


class CoursePreviewView(APIView):
    """GET /api/v1/courses/{slug}/preview/ — bepul sinab ko'rish darslari."""

    permission_classes = [IsAuthenticated, IsApprovedStudent]

    def get(self, request, slug):
        course = selectors.get_published_course(slug=slug)
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        lessons = selectors.get_free_preview_lessons(course)
        return Response(
            LessonDetailSerializer(lessons, many=True, context={"request": request}).data,
        )


class CourseEnrollView(APIView):
    """
    POST /api/v1/courses/{slug}/enroll/
    Bepul kurslar uchun bevosita enrollment; pullik kurslar
    /api/v1/payments/checkout/ orqali (P01-P10 to'lov oqimi).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        course = selectors.get_published_course(slug=slug)
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if course.price > 0:
            return Response(
                {"detail": "Pullik kurs — /api/v1/payments/checkout/ orqali sotib oling",
                 "checkout_required": True},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        from apps.enrollment.services import enroll_free

        try:
            enrollment = enroll_free(user=request.user, course=course)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response({"enrollment_id": str(enrollment.id)}, status=status.HTTP_201_CREATED)
