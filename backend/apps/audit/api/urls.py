from rest_framework.routers import DefaultRouter

from apps.audit.api.views import AuditLogViewSet, ReportsViewSet

router = DefaultRouter()
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("reports", ReportsViewSet, basename="report")

urlpatterns = router.urls
