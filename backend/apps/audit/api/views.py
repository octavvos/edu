from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.api.serializers import AuditLogSerializer
from apps.audit.models import AuditLog
from apps.core.pagination import AdminPageNumberPagination
from apps.core.permissions import HasPermission


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """AD-08: audit-log ko'rinishi (faqat o'qish, append-only)."""

    queryset = AuditLog.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    pagination_class = AdminPageNumberPagination
    permission_classes = [HasPermission]
    required_permission = "audit.view"
    filterset_fields = ("action", "object_type", "actor")


class ReportsViewSet(viewsets.ViewSet):
    """AD-05: DAU/MAU, daromad, konversiya voronkasi va h.k."""

    permission_classes = [HasPermission]
    required_permission = "report.view"

    @action(detail=False, methods=["get"])
    def summary(self, request):
        from apps.analytics.selectors import get_admin_dashboard_summary

        return Response(get_admin_dashboard_summary())
