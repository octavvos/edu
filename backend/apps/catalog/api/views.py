from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog import selectors, services
from apps.catalog.api.serializers import (
    CategorySerializer,
    CourseCardSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
)
from apps.core.exceptions import DomainError


class CategoryListView(APIView):
    """K-01"""

    permission_classes = [AllowAny]

    def get(self, request):
        roots, by_parent = selectors.get_category_tree()
        serializer = CategorySerializer(roots, many=True, context={"by_parent": by_parent})
        return Response(serializer.data)


class CourseSearchView(APIView):
    """K-02, K-03, K-04: filtrlar, saralash, typo-tolerant qidiruv."""

    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        qs = selectors.search_courses(
            query=request.query_params.get("q", ""),
            category_slug=request.query_params.get("category", ""),
            price=request.query_params.get("price", ""),
            level=request.query_params.get("level", ""),
            language=request.query_params.get("language", ""),
            min_rating=request.query_params.get("min_rating") or None,
            has_certificate=_parse_bool(request.query_params.get("has_certificate")),
            ordering=request.query_params.get("ordering", "popular"),
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        data = CourseCardSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


def _parse_bool(value):
    if value is None:
        return None
    return value.lower() in ("1", "true", "yes")


class RecommendationsView(APIView):
    """K-05"""

    permission_classes = [AllowAny]

    def get(self, request, course_id):
        from apps.courses.models import Course

        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(selectors.get_recommendations(course))


class CourseReviewListCreateView(APIView):
    """K-08"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, course_id):
        from apps.courses.models import Course

        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        reviews = selectors.get_course_reviews(course)
        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request, course_id):
        from apps.courses.models import Course

        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = services.submit_review(user=request.user, course=course, **serializer.validated_data)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
