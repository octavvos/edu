from rest_framework.pagination import CursorPagination, PageNumberPagination


class CursorSetPagination(CursorPagination):
    """Katalog/feed uchun (TZ 5.6) — cursor-based pagination."""

    page_size = 20
    ordering = "-created_at"
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminPageNumberPagination(PageNumberPagination):
    """Admin ro'yxatlari uchun (TZ 5.6) — page-based pagination."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200
